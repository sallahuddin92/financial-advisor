# Malaysia FSI Product Readiness Audit

Audit date: 2026-05-08
Repository: `/Users/sallahuddin/financial-services`
Scope reviewed:
- `README-MY.md`
- `IMPLEMENTATION_STATUS.md`
- `MVP_SCOPE.md`
- `TODO.md`
- `docs/malaysia-fsi/*`
- `malaysia_fsi/bank_statement/*`
- `malaysia_fsi/receipts/*`
- `tests/*`
- `scripts/verify_malaysia_fsi.py`
- `.github/workflows/malaysia-fsi-ci.yml`

Validation executed before audit:
- `python3 -m pytest -v` (60 passed)
- `python3 scripts/validate_malaysia_phase1.py` (49/49 passed)
- `python3 scripts/verify_malaysia_fsi.py` (passed)

## 1. Current product identity
This is an **offline Malaysian SME finance assistant** for:
- Bank statement parsing (currently Maybank CSV)
- Invoice matching and reconciliation reporting
- Manual/JSON receipt categorization and monthly expense summaries

It is **not** an automated accounting/tax/compliance engine. It is positioned as decision support with explicit human-review-required guardrails.

## 2. Actual implemented user flows
1. Parse bank CSV:
   - `python3 -m malaysia_fsi.bank_statement.cli parse <csv> [--json]`
2. Match statement vs invoices:
   - `python3 -m malaysia_fsi.bank_statement.cli match <csv> <invoice-file-or-dir> [--json|--format csv|md]`
3. Validate statement/invoice inputs:
   - `python3 -m malaysia_fsi.bank_statement.cli validate --input <csv> --invoice <json>`
4. Categorize receipts (JSON/manual input):
   - `python3 -m malaysia_fsi.receipts.cli categorize <receipt-file-or-dir> [--json]`
5. Build monthly receipt summaries:
   - `python3 -m malaysia_fsi.receipts.cli summarize <receipt-file-or-dir> [--format json|csv|md]`
6. Validate receipt payloads:
   - `python3 -m malaysia_fsi.receipts.cli validate --receipt <json...>`
7. Legacy plugin wrapper CLIs for parser/matcher still execute as compatibility shims.

## 3. What works end-to-end today
1. Maybank CSV -> normalized transactions with warning codes.
2. Invoice matching with status buckets (`matched`, `possible_match`, `unmatched`, `overpaid`, `underpaid`).
3. Reconciliation report export to JSON/CSV/Markdown.
4. Receipt JSON ingestion -> rule-based categorization -> duplicate candidate detection.
5. Monthly summary export to JSON/CSV/Markdown.
6. Unmatched transaction advisory category hints in reconciliation report.
7. CI + local verification script + full test suite all pass.

## 4. What is still placeholder
1. Bank parsing beyond Maybank: CIMB/Public Bank/RHB/Hong Leong are intentionally disabled placeholders.
2. Institutional finance plugin directories are README-only placeholders.
3. MyInvois/SSM/JPN/BNM/CTOS/Bursa/bank API integration: not implemented.
4. OCR/PDF/image receipt ingestion: not implemented.
5. Any automated regulatory/accounting sign-off: not implemented.

## 5. Top 10 correctness risks
1. **Money type inconsistency**: bank statement transaction amounts are `float`; receipts use `Decimal`. Mixed arithmetic increases long-tail rounding risk.
2. **CSV dialect sniff fragility**: `csv.Sniffer` can mis-detect delimiters on unusual files and silently skew parsing behavior.
3. **Date parsing narrowness**: parser supports limited date formats; real-world bank exports may break or partially parse.
4. **Invoice matching heuristic opacity at boundaries**: score thresholds can flip status between `possible_match` and `matched/overpaid/underpaid` in unintuitive ways.
5. **No one-to-one assignment constraint**: same invoice can effectively be considered across multiple transactions without hard uniqueness control.
6. **Invalid money fallback behavior**: some invalid values normalize to zero paths that are warned but still flow through downstream logic.
7. **Receipt keyword collisions**: keyword overlap (e.g., delivery vs packaging terms) can produce unstable category assignment.
8. **Duplicate receipt detection key simplicity**: merchant+date+amount can over-flag legitimate repeat purchases.
9. **Limited fuzz/volume testing**: tests are strong unit tests but weak on large, messy real-world input distributions.
10. **Schema-level contract drift risk**: JSON output is not formally versioned; consumers may break if fields evolve.

## 6. Top 10 usability gaps
1. No guided onboarding wizard for non-technical SME users.
2. CLI ergonomics are developer-centric; little contextual remediation help on errors.
3. No localized language support (BM/EN mixed UX).
4. No interactive review queue for warnings/possible matches.
5. No stable artifact directory convention (outputs often written to `/tmp` ad hoc).
6. No command to inspect/edit category rules at runtime.
7. No explainability block showing exactly why a category was selected (keyword hit breakdown).
8. No summary dashboard command combining reconciliation + receipts into one monthly pack.
9. Strict mode behavior is not fully documented as an operator runbook.
10. No packaging/distribution path for non-developer install experience.

## 7. Top 10 compliance/safety risks
1. Users may over-trust "matched" as accounting truth despite disclaimers.
2. Heuristic category suggestions may be mistaken for tax-deductibility advice.
3. No immutable audit trail/signature for report outputs.
4. No data retention policy controls (especially if run on shared machines).
5. No role-based access model (single-user CLI assumption).
6. No PII redaction pipeline for imported receipts/invoices.
7. No explicit legal/regulatory version pinning in outputs.
8. No policy gate preventing use of reports as filing-ready artifacts.
9. Warning severity is not tiered (all warnings are flat, reducing triage quality).
10. No independent accountant/compliance acceptance test suite yet.

## 8. Recommended next 5 build tasks (ranked)
1. **Unify money handling to Decimal across bank + matcher + report paths** and add regression tests for edge rounding.
2. **Add one-to-one reconciliation constraints + duplicate invoice usage warnings** to prevent over-counting matches.
3. **Add explainability payloads** for both matching and categorization (scores, keyword hits, rule ids).
4. **Add high-volume/chaos fixture suite** (thousands of rows, malformed variants, mixed encodings, noisy descriptions).
5. **Add operator runbook + CLI safety UX improvements** (error remediation text, strict-mode guidance, standardized output directories).

## 9. What NOT to build yet
1. Any live API integrations (MyInvois/SSM/JPN/BNM/CTOS/Bursa/bank APIs).
2. Automated filing/submission workflows.
3. Automated compliance or accounting decision engines.
4. Institutional finance functionality beyond current placeholder architecture.
5. OCR/PDF ingestion until quality, privacy, and error-handling guardrails are formalized.

## 10. Go / No-Go status
- **Internal demo**: **GO (with caveats)**
  - Reason: stable offline flows, passing tests, clear disclaimers.
- **Accountant review demo**: **GO (with caveats)**
  - Reason: useful for assisted review; must frame outputs as advisory only.
- **SME pilot**: **CONDITIONAL GO (small controlled pilot only)**
  - Conditions: trained operator, explicit human review checklist, no filing automation, narrow user profile.
- **Paid SaaS**: **NO-GO**
  - Reason: missing tenancy/security/compliance controls, auditability, supportability, and legal readiness.
- **Institutional finance demo**: **NO-GO**
  - Reason: institutional lane is placeholder architecture only, no implemented workflows.

## Bottom line
This repo is a **credible offline MVP assistant for supervised SME reconciliation and receipt categorization**, not a production-grade autonomous finance system. It is suitable for demos and constrained pilot learning, but not for paid SaaS or institutional use in current form.
