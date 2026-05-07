---
name: my-kyc-checklist
description: Malaysian KYC verification checklist based on Bank Negara Malaysia AML/CFT guidelines and manual verification workflows.
---

# Malaysian KYC Verification Checklist

Provides KYC verification checklists based on Bank Negara Malaysia AML/CFT guidelines for manual processing.

⚠️ **CURRENT STATUS: PLACEHOLDER IMPLEMENTATION** ⚠️
This skill provides the framework for Malaysian KYC checking but requires additional development for production use.

## TODO: Implementation Required

- [ ] BNM AML/CFT guideline implementation
- [ ] Risk factor assessment logic
- [ ] Document requirement mapping
- [ ] Enhanced due diligence triggers
- [ ] PEP screening reference framework
- [ ] Sanctions list checking workflow
- [ ] Risk scoring algorithm

## Current Capabilities (Placeholder)

- Framework for checklist generation
- Risk factor identification structure
- Document requirement templates
- Manual verification workflow documentation

## KYC Risk Factors (Malaysian Context)

### Customer Risk Factors
- [ ] Jurisdiction risk (customer nationality/residence)
- [ ] Business sector risk
- [ ] Legal structure complexity
- [ ] Ownership transparency

### Product/Service Risk Factors
- [ ] Transaction complexity
- [ ] Cross-border exposure
- [ ] Cash-intensive business
- [ ] Politically Exposed Person (PEP) connection

### Geographic Risk Factors
- [ ] High-risk jurisdictions
- [ ] Sanctioned countries
- [ ] Money laundering risk areas

## Document Requirements by Entity Type

| Entity Type | Required Documents | Enhanced Requirements |
|-------------|-------------------|----------------------|
| Individual | MyKad, proof of address | Source of funds, income verification |
| Company | SSM docs, board resolution | UBO declaration, source of funds |
| Partnership | Partnership agreement | Partner IDs, business license |
| Trust | Trust deed, trustee IDs | Settlor info, beneficiary details |

## Risk Rating Framework

### Low Risk
- Malaysian citizens/residents
- Simple business structures
- Transparent ownership
- Local transactions only

### Medium Risk
- Foreign customers (non-high-risk)
- Moderate complexity structures
- Some cross-border activity
- Professional services

### High Risk
- PEP connections
- High-risk jurisdictions
- Complex ownership structures
- High-value transactions
- Cash-intensive businesses

## Output Format

```json
{
  "risk_rating": "low|medium|high|review",
  "checklist_completion": 75,
  "missing_documents": ["ubo_declaration", "source_of_funds"],
  "risk_factors": ["foreign_customer", "cross_border"],
  "edd_required": true,
  "recommendations": [
    "Obtain UBO declaration",
    "Verify source of funds documentation",
    "Enhanced monitoring recommended"
  ]
}
```

## Important Limitations

- ❌ No real-time screening database access
- ❌ No automatic PEP/sanctions checking
- ❌ No live risk updates
- ✅ Manual checklist generation
- ✅ Risk factor identification
- ✅ Document requirement guidance

⚠️ **HUMAN REVIEW REQUIRED** ⚠️
All KYC assessments and risk ratings must be verified by qualified compliance officers.
This system provides assistance only and does not replace professional compliance judgment.