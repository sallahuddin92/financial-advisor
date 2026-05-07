---
name: ssm-doc-parse
description: Parser for SSM (Companies Commission of Malaysia) documents including Form 24, Form 49, business registration certificates, and annual returns.
---

# SSM Document Parser

Processes manually uploaded SSM documents to extract company and business registration information.

⚠️ **CURRENT STATUS: PLACEHOLDER IMPLEMENTATION** ⚠️
This skill provides the framework for SSM document parsing but requires additional development for production use.

## TODO: Implementation Required

- [ ] Form 24 parser (Notice of situation of registered office)
- [ ] Form 49 parser (Particulars of directors)
- [ ] Business registration certificate parser
- [ ] Annual return parser
- [ ] OCR integration for scanned documents
- [ ] Data validation and cross-referencing
- [ ] Document authenticity verification workflow

## Current Capabilities (Placeholder)

- Framework for document type detection
- Data extraction structure definitions
- Document validity checking methodology
- Manual verification workflow documentation

## Supported Document Types

| Document | Purpose | Key Information Extracted |
|----------|---------|---------------------------|
| Form 24 | Registered office notice | Company address, registration details |
| Form 49 | Director particulars | Director names, addresses, appointments |
| Business Certificate | Registration proof | Business name, number, status |
| Annual Return | Annual filing | Financial summary, shareholder info |

## Data Extraction Structure

```json
{
  "document_type": "Form 24",
  "document_number": "SSA-FED-0001234567",
  "extraction_date": "2024-01-15",
  "company_info": {
    "name": "Example Sdn Bhd",
    "registration_number": "123456-K",
    "incorporation_date": "2020-01-01",
    "status": "Active"
  },
  "address_info": {
    "registered_office": "123 Main Street, Kuala Lumpur"
  },
  "validity_check": {
    "document_authentic": "Requires manual verification",
    "cross_reference_status": "Pending"
  }
}
```

## Verification Workflow

Since real-time SSM API access is not available:

1. **Document Upload**: User uploads SSM document PDF/image
2. **Data Extraction**: System extracts visible information
3. **Authenticity Flags**: System highlights items requiring verification
4. **Manual Cross-Check**: User verifies against official SSM portal
5. **Validation Report**: System compiles verification status

## Important Limitations

- ❌ No real-time SSM database access
- ❌ No automatic authenticity verification
- ❌ No live status updates
- ✅ Manual document processing only
- ✅ Reference information extraction

## Manual Verification Required

All extracted information requires:
- Cross-checking against official SSM portal
- Verification of document authenticity
- Confirmation of current status

⚠️ **HUMAN REVIEW REQUIRED** ⚠️
All SSM document information must be verified against official sources.
This system assists with data extraction but does not replace official verification.