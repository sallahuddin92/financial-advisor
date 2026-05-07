# Production-Readiness Checklist (Offline MVP)

## Completed

- [x] Importable package structure
- [x] Parser + matcher + reporting tests
- [x] Structured warning codes
- [x] Unified CLI with safe failure modes
- [x] Verification script (`scripts/verify_malaysia_fsi.py`)
- [x] CI workflow

## Remaining Before Broader Deployment

- [ ] Larger anonymized fixture diversity
- [ ] Operational runbook for strict mode and exception handling
- [ ] Governance sign-off for human review workflows

## Permanent Constraints

- Maybank CSV is currently the only real implemented bank format.
- Other banks are disabled placeholders pending anonymized fixtures.
- No government or external API integrations are included.
- Institutional finance plugin lanes are placeholders only in current scope.
