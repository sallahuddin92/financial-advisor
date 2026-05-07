---
name: sst-checklist
description: SST and e-Invoice compliance checklist based on Royal Malaysian Customs Department and LHDN requirements.
---

# SST/e-Invoice Compliance Checklist

Provides compliance checking for Sales and Service Tax (SST) and e-Invoice requirements in Malaysia.

⚠️ **CURRENT STATUS: PLACEHOLDER IMPLEMENTATION** ⚠️
This skill provides the framework for SST compliance checking but requires additional development for production use.

## TODO: Implementation Required

- [ ] Current SST rate implementation (effective 2024)
- [ ] e-Invoice mandatory field validation
- [ ] Tax code mapping and validation
- [ ] Calculation verification logic
- [ ] Submission deadline tracking
- [ ] Exception handling for edge cases

## Current Capabilities (Placeholder)

- Framework for compliance rule checking
- Checklist generation structure
- Gap identification methodology
- Reference documentation links

## SST Compliance Areas

### Tax Calculation
- [ ] Correct SST rate application
- [ ] Taxable vs non-taxable items
- [ ] Exempt supply identification
- [ ] Zero-rated supply verification

### e-Invoice Requirements
- [ ] Mandatory fields completion
- [ ] Invoice numbering compliance
- [ ] Date and time accuracy
- [ ] Supplier/customer information

### Documentation
- [ ] Supporting document availability
- [ ] Record retention compliance
- [ ] Audit trail completeness

## Compliance Scoring

Each item scored as:
- **Pass**: Requirement met
- **Fail**: Requirement not met
- **Review**: Requires manual verification
- **N/A**: Not applicable for this transaction

## Output Format

```json
{
  "overall_compliance": "pass|fail|review",
  "sst_score": 85,
  "e_invoice_score": 92,
  "missing_items": ["tax_code", "customer_gst_number"],
  "recommendations": ["Update tax code mapping", "Verify customer GST registration"]
}
```

## Reference Sources

- Royal Malaysian Customs Department guidelines
- LHDN MyInvois documentation
- SST Act 2018 and amendments

⚠️ **HUMAN REVIEW REQUIRED** ⚠️
All compliance assessments must be verified against current regulations.
This system provides assistance only and does not guarantee compliance.