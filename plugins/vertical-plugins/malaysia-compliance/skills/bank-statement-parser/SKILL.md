---
name: bank-statement-parser
description: Parser for Malaysian bank statement CSV/XLSX files from major banks. Extracts transactions and normalizes data for reconciliation.
---

# Malaysian Bank Statement Parser

Supports CSV/XLSX import from major Malaysian banks for transaction extraction and reconciliation.

⚠️ **CURRENT STATUS: PARTIALLY IMPLEMENTED** ⚠️
This skill provides a working CSV parser for Maybank statements with framework for additional banks.

## ✅ Implemented

- [x] Maybank CSV format parser
- [x] Multi-bank parser registry/factory architecture
- [x] Auto-detection framework (Maybank detection enabled)
- [x] Disabled parser placeholders (CIMB, Public Bank, RHB, Hong Leong Bank)
- [x] Data validation and error handling
- [x] Currency and date normalization
- [x] Standard transaction schema
- [x] Invoice matching system
- [x] CLI interface for testing
- [x] CLI interface for invoice matching
- [x] Unit tests for sample data
- [x] Unit tests for invoice matching

## TODO: Implementation Required

- [ ] CIMB CSV parsing implementation (currently disabled placeholder)
- [ ] Public Bank CSV parsing implementation (currently disabled placeholder)
- [ ] RHB CSV parsing implementation (currently disabled placeholder)
- [ ] Hong Leong Bank CSV parsing implementation (currently disabled placeholder)
- [ ] XLSX format support for all banks
- [ ] Enhanced error recovery
- [ ] Advanced matching algorithms

## Current Capabilities

- ✅ **Maybank CSV parsing**: Full support for Maybank CSV format
- ✅ **Parser architecture**: Registry/factory design with explicit enabled/disabled bank statuses
- ✅ **Guarded placeholders**: Unimplemented banks raise `NotImplementedError` with clear fixture requirement
- ✅ **Standard schema**: Normalized transaction output with confidence scores
- ✅ **Invoice matching**: Match transactions to invoice JSON files using amount, date, and keyword analysis
- ✅ **Error handling**: Robust parsing with warnings for problematic rows
- ✅ **CLI tools**: Command-line interfaces for parsing and matching validation
- ✅ **Unit tests**: Comprehensive test coverage for parsing and matching
- ✅ **Manual verification**: All outputs include human review requirements

## Supported Bank Formats

| Bank | CSV Support | XLSX Support | Notes |
|------|-------------|--------------|-------|
| Maybank | ✅ Implemented | ❌ Planned | Most common format |
| CIMB | 🚫 Disabled placeholder | ❌ Planned | Requires real anonymized fixture |
| Public Bank | 🚫 Disabled placeholder | ❌ Planned | Requires real anonymized fixture |
| RHB | 🚫 Disabled placeholder | ❌ Planned | Requires real anonymized fixture |
| Hong Leong | 🚫 Disabled placeholder | ❌ Planned | Requires real anonymized fixture |

## Data Extraction

Standard transaction schema output:
```json
{
  "bank_name": "Maybank",
  "statement_period": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "currency": "MYR",
  "confidence": 0.9,
  "warnings": [],
  "transaction_count": 10,
  "transactions": [
    {
      "date": "2024-01-15",
      "description": "Payment to supplier",
      "debit": 1000.00,
      "credit": null,
      "amount": -1000.00,
      "direction": "debit",
      "balance": 5000.00,
      "currency": "MYR",
      "source_bank": "Maybank",
      "confidence": 0.9,
      "warnings": []
    }
  ]
}
```

## Reconciliation Support

- **Invoice matching**: Match bank transactions to invoice data using:
  - Amount comparison with tolerance
  - Date proximity analysis
  - Keyword similarity (supplier/customer names)
  - Invoice number detection
- **Match status classification**:
  - ✅ matched: High confidence match
  - 🤔 possible_match: Medium confidence match
  - ❌ unmatched: No suitable match found
  - 💰 overpaid: Transaction amount exceeds invoice
  - 💸 underpaid: Transaction amount below invoice
- **Confidence scoring**: 0.0 to 1.0 confidence for each match
- **Warning system**: Identifies potential issues for manual review

⚠️ **HUMAN REVIEW REQUIRED** ⚠️
All parsed data must be verified against original bank statements.
This system assists with data extraction but does not replace manual verification.
