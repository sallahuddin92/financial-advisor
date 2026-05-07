# Bank Statement Parser

## Scope

The offline parser currently implements **Maybank CSV** only.

Other banks are architecture placeholders and disabled until real anonymized fixtures are provided:
- CIMB
- Public Bank
- RHB
- Hong Leong Bank

## Safety Posture

- No live bank feeds
- No bank APIs
- No automated approvals
- Human review required for all parsed outputs

## Command

```bash
python3 -m malaysia_fsi.bank_statement.cli parse test-fixtures/sample-data/maybank-valid.csv --json
```
