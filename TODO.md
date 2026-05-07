# Implementation TODO List

## Current State (Offline Reconciliation MVP)

### Completed ✅
- [x] Importable package: `malaysia_fsi.bank_statement`
- [x] Maybank CSV parsing (offline)
- [x] Invoice matcher and reconciliation summaries
- [x] Multi-bank parser architecture with disabled placeholders
- [x] Structured warning codes and validation hardening
- [x] CLI (`parse`, `match`, `validate`) with JSON output and safe failure modes
- [x] Report exporters: JSON, CSV, Markdown
- [x] Expanded anonymized fixture suite
- [x] Verification script and CI workflow
- [x] Receipt schema and warning-code foundation for SME expense lane

### Next Small Tasks 🔄
- [ ] Implement receipt categorizer rules and duplicate detection
- [ ] Build monthly expense summary reports (JSON/CSV/Markdown)
- [ ] Add receipt CLI (`categorize`, `summarize`, `validate`)
- [ ] Add larger anonymized Maybank fixture variants for high-volume testing
- [ ] Add deterministic snapshot tests for Markdown and CSV reports
- [ ] Add changelog/release-note template for offline MVP releases
- [ ] Add tighter CLI operator runbook for strict-mode usage

## Explicitly Out of Scope (Current)

- [ ] MyInvois API integration
- [ ] SSM/JPN/BNM verification integrations
- [ ] CTOS/Bursa/bank API integrations
- [ ] Automated compliance determinations
- [ ] Regulatory/tax/accounting decision automation

## Important Notes

- All outputs must include **HUMAN REVIEW REQUIRED** posture.
- This module is offline reconciliation assistance only.
- Maybank CSV is the only implemented real bank format.
- Other banks remain placeholders until real anonymized fixtures are available.
