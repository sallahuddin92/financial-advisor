---
name: bank-statement-parser
description: Parser for Malaysian bank statement CSV/XLSX files from major banks. Extracts transactions and normalizes data for reconciliation.
---

# Malaysian Bank Statement Parser

Supports CSV/XLSX import from major Malaysian banks for transaction extraction and reconciliation.

⚠️ **CURRENT STATUS: PLACEHOLDER IMPLEMENTATION** ⚠️
This skill provides the framework for bank statement parsing but requires additional development for production use.

## TODO: Implementation Required

- [ ] Maybank CSV format parser
- [ ] CIMB CSV format parser
- [ ] Public Bank CSV format parser
- [ ] RHB CSV format parser
- [ ] Hong Leong Bank CSV format parser
- [ ] XLSX format support for all banks
- [ ] Data validation and error handling
- [ ] Currency and date normalization

## Current Capabilities (Placeholder)

- Framework for bank-specific parsers
- Sample data structure definitions
- Format detection logic outline
- Data normalization utilities

## Supported Bank Formats (Planned)

| Bank | CSV Support | XLSX Support | Notes |
|------|-------------|--------------|-------|
| Maybank | ✅ Planned | ✅ Planned | Most common format |
| CIMB | ✅ Planned | ✅ Planned | Multiple variants |
| Public Bank | ✅ Planned | ✅ Planned | Standard format |
| RHB | ✅ Planned | ✅ Planned | Standard format |
| Hong Leong | ✅ Planned | ✅ Planned | Standard format |

## Data Extraction

Expected output structure:
```json
{
  "bank_name": "Maybank",
  "account_number": "****1234",
  "statement_period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "transactions": [
    {
      "date": "2024-01-15",
      "description": "Payment to supplier",
      "amount": -1000.00,
      "balance": 5000.00,
      "reference": "INV001"
    }
  ]
}
```

## Reconciliation Support

- Transaction matching algorithms
- Variance detection
- Missing transaction identification
- Duplicate detection

⚠️ **HUMAN REVIEW REQUIRED** ⚠️
All parsed data must be verified against original bank statements.
This system assists with data extraction but does not replace manual verification.