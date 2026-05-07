"""Invoice matching system for Malaysian bank statements."""

import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .schema import BankStatement, Transaction


class MatchResult:
    """Result of invoice matching operation."""

    def __init__(self, status: str, confidence: float, warnings: Optional[List[str]] = None):
        self.status = status
        self.confidence = confidence
        self.warnings = warnings or []
        self.matched_amount = 0.0
        self.expected_amount = 0.0
        self.matched_transaction = None
        self.matched_invoice = None


class InvoiceMatcher:
    """Matches bank transactions with invoice data."""

    def __init__(self, date_tolerance_days: int = 3, amount_tolerance_percent: float = 0.01):
        self.date_tolerance = timedelta(days=date_tolerance_days)
        self.amount_tolerance = amount_tolerance_percent

    def load_invoice(self, invoice_path: Path) -> Optional[Dict]:
        try:
            with open(invoice_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return None

    def extract_keywords(self, text: str) -> List[str]:
        if not text:
            return []

        words = re.findall(r"\b\w+\b", text.lower())
        stop_words = {"the", "and", "or", "for", "to", "of", "in", "on", "at", "by", "with", "from"}
        return [word for word in words if len(word) > 2 and word not in stop_words]

    def calculate_date_score(self, tx_date: date, invoice_date: Optional[date]) -> float:
        if not invoice_date:
            return 0.5

        days_diff = abs((tx_date - invoice_date).days)
        if days_diff == 0:
            return 1.0
        if days_diff <= 1:
            return 0.9
        if days_diff <= 3:
            return 0.7
        if days_diff <= 7:
            return 0.5
        if days_diff <= self.date_tolerance.days:
            return 0.3
        return 0.0

    def calculate_amount_score(self, tx_amount: float, invoice_amount: float) -> float:
        if invoice_amount == 0:
            return 0.0

        difference = abs(tx_amount - invoice_amount)
        tolerance = invoice_amount * self.amount_tolerance

        if difference <= tolerance:
            return 1.0
        if difference <= tolerance * 2:
            return 0.8
        if difference <= invoice_amount * 0.05:
            return 0.6
        if difference <= invoice_amount * 0.10:
            return 0.4
        return 0.0

    def calculate_keyword_score(self, tx_description: str, invoice_texts: List[str]) -> float:
        if not tx_description or not invoice_texts:
            return 0.5

        tx_keywords = set(self.extract_keywords(tx_description))
        if not tx_keywords:
            return 0.5

        max_score = 0.0
        for invoice_text in invoice_texts:
            invoice_keywords = set(self.extract_keywords(invoice_text))
            if not invoice_keywords:
                continue
            intersection = tx_keywords.intersection(invoice_keywords)
            union = tx_keywords.union(invoice_keywords)
            if union:
                similarity = len(intersection) / len(union)
                max_score = max(max_score, similarity)

        return max_score

    def find_invoice_number_match(self, tx_description: str, invoice_number: str) -> float:
        if not invoice_number or not tx_description:
            return 0.0

        patterns = [
            invoice_number.lower(),
            invoice_number.replace("-", "").lower(),
            invoice_number.replace("inv", "").lower(),
        ]
        tx_lower = tx_description.lower()
        for pattern in patterns:
            if pattern in tx_lower:
                return 1.0
        return 0.0

    def match_transaction_to_invoice(self, transaction: Transaction, invoice: Dict) -> MatchResult:
        result = MatchResult("unmatched", 0.0)

        invoice_amount = invoice.get("grand_total", 0.0)
        invoice_date_str = invoice.get("date")
        invoice_date = None
        if invoice_date_str:
            try:
                invoice_date = date.fromisoformat(invoice_date_str)
            except (ValueError, TypeError):
                pass

        invoice_number = invoice.get("invoice_number", "")
        supplier_name = invoice.get("supplier", {}).get("name", "")
        customer_name = invoice.get("customer", {}).get("name", "")

        tx_amount_abs = abs(transaction.amount or 0)

        date_score = self.calculate_date_score(transaction.date, invoice_date)
        amount_score = self.calculate_amount_score(tx_amount_abs, invoice_amount)
        keyword_texts = [supplier_name, customer_name] + [
            item.get("description", "") for item in invoice.get("items", [])
        ]
        keyword_score = self.calculate_keyword_score(transaction.description, keyword_texts)
        invoice_number_score = self.find_invoice_number_match(transaction.description, invoice_number)

        overall_score = (
            amount_score * 0.4 + date_score * 0.25 + keyword_score * 0.2 + invoice_number_score * 0.15
        )

        amount_difference = tx_amount_abs - invoice_amount
        amount_difference_percent = abs(amount_difference) / invoice_amount if invoice_amount > 0 else 0

        if amount_score >= 0.8 and overall_score >= 0.7:
            if amount_difference_percent <= 0.02:
                result.status = "matched"
                result.confidence = overall_score
            elif amount_difference > 0:
                result.status = "overpaid"
                result.confidence = overall_score * 0.8
            elif amount_difference < 0:
                result.status = "underpaid"
                result.confidence = overall_score * 0.8
            else:
                result.status = "possible_match"
                result.confidence = overall_score
        elif overall_score >= 0.5:
            result.status = "possible_match"
            result.confidence = overall_score
        else:
            result.status = "unmatched"
            result.confidence = overall_score

        result.matched_amount = tx_amount_abs
        result.expected_amount = invoice_amount
        result.matched_transaction = transaction
        result.matched_invoice = invoice

        if amount_difference_percent > 0.05:
            result.warnings.append(f"Amount difference: {amount_difference_percent:.1%}")
        elif amount_difference_percent > self.amount_tolerance:
            result.warnings.append(f"Near amount match: {amount_difference_percent:.1%} difference")
        if date_score < 0.5:
            result.warnings.append("Date mismatch beyond tolerance")
        if keyword_score < 0.3:
            result.warnings.append("Low keyword similarity")

        return result

    def match_statement_to_invoices(self, statement: BankStatement, invoice_paths: List[Path]) -> List[MatchResult]:
        results: List[MatchResult] = []
        loaded_invoices = []

        for invoice_path in invoice_paths:
            invoice = self.load_invoice(invoice_path)
            if invoice:
                loaded_invoices.append(invoice)
            else:
                results.append(MatchResult("unmatched", 0.0, [f"Failed to load invoice: {invoice_path}"]))

        for transaction in statement.transactions:
            best_match = None
            best_score = 0.0
            second_best_score = 0.0

            for invoice in loaded_invoices:
                match_result = self.match_transaction_to_invoice(transaction, invoice)
                if match_result.confidence > best_score:
                    second_best_score = best_score
                    best_match = match_result
                    best_score = match_result.confidence
                elif match_result.confidence > second_best_score:
                    second_best_score = match_result.confidence

            if best_match:
                if best_score >= 0.5 and (best_score - second_best_score) <= 0.02:
                    best_match.warnings.append(
                        "Multiple candidate invoices with similar confidence; manual review required"
                    )
                results.append(best_match)
            else:
                no_match = MatchResult("unmatched", 0.0)
                no_match.matched_transaction = transaction
                no_match.warnings.append("No matching invoice found")
                results.append(no_match)

        return results

    def generate_matching_report(self, results: List[MatchResult]) -> Dict:
        report = {
            "total_transactions": len(results),
            "matched": 0,
            "possible_matches": 0,
            "unmatched": 0,
            "overpaid": 0,
            "underpaid": 0,
            "total_confidence": 0.0,
            "average_confidence": 0.0,
            "warnings": [],
            "details": [],
        }

        for result in results:
            if result.status == "matched":
                report["matched"] += 1
            elif result.status == "possible_match":
                report["possible_matches"] += 1
            elif result.status == "unmatched":
                report["unmatched"] += 1
            elif result.status == "overpaid":
                report["overpaid"] += 1
            elif result.status == "underpaid":
                report["underpaid"] += 1

            report["total_confidence"] += result.confidence
            report["warnings"].extend(result.warnings)

            detail = {
                "status": result.status,
                "confidence": round(result.confidence, 3),
                "transaction_date": result.matched_transaction.date.isoformat()
                if result.matched_transaction
                else None,
                "transaction_description": result.matched_transaction.description
                if result.matched_transaction
                else None,
                "transaction_amount": result.matched_amount,
                "expected_amount": result.expected_amount,
                "difference": result.matched_amount - result.expected_amount,
                "warnings": result.warnings,
            }
            report["details"].append(detail)

        if results:
            report["average_confidence"] = report["total_confidence"] / len(results)

        return report

    def build_reconciliation_report(
        self, statement: BankStatement, results: List[MatchResult], invoices: List[Dict]
    ) -> Dict:
        status_counts = {
            "matched_count": 0,
            "possible_match_count": 0,
            "unmatched_count": 0,
            "overpaid_count": 0,
            "underpaid_count": 0,
        }
        total_matched_amount = 0.0
        warnings = list(statement.warnings or [])

        matched_invoice_keys = set()
        invoice_totals_by_key = {}

        for idx, invoice in enumerate(invoices):
            invoice_number = invoice.get("invoice_number")
            invoice_key = invoice_number if invoice_number else f"invoice_index_{idx}"
            invoice_totals_by_key[invoice_key] = float(invoice.get("grand_total", 0.0) or 0.0)

        for result in results:
            status_key = f"{result.status}_count"
            if status_key in status_counts:
                status_counts[status_key] += 1

            if result.status in {"matched", "possible_match", "overpaid", "underpaid"}:
                total_matched_amount += float(result.matched_amount or 0.0)
                if result.matched_invoice:
                    invoice_number = result.matched_invoice.get("invoice_number")
                    if invoice_number and invoice_number in invoice_totals_by_key:
                        matched_invoice_keys.add(invoice_number)
                    else:
                        for idx, invoice in enumerate(invoices):
                            if invoice is result.matched_invoice:
                                matched_invoice_keys.add(f"invoice_index_{idx}")
                                break

            warnings.extend(result.warnings or [])

        unmatched_invoice_keys = set(invoice_totals_by_key.keys()) - matched_invoice_keys
        total_unmatched_invoice_amount = sum(invoice_totals_by_key[key] for key in unmatched_invoice_keys)

        return {
            "statement_bank": statement.bank_name,
            "statement_period": {
                "start": statement.statement_period_start.isoformat()
                if statement.statement_period_start
                else None,
                "end": statement.statement_period_end.isoformat()
                if statement.statement_period_end
                else None,
            },
            "total_transactions": len(statement.transactions or []),
            "total_invoices": len(invoices),
            "matched_count": status_counts["matched_count"],
            "possible_match_count": status_counts["possible_match_count"],
            "unmatched_count": status_counts["unmatched_count"],
            "overpaid_count": status_counts["overpaid_count"],
            "underpaid_count": status_counts["underpaid_count"],
            "total_matched_amount": round(total_matched_amount, 2),
            "total_unmatched_invoice_amount": round(total_unmatched_invoice_amount, 2),
            "warnings": sorted(set(warnings)),
            "human_review_required": True,
        }
