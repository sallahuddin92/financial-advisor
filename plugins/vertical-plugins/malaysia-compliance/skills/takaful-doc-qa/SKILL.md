---
name: takaful-doc-qa
description: Q&A system for Malaysian Takaful documents and Islamic finance principles. Extracts information from uploaded PDFs for reference purposes.
---

# Takaful Document Q&A System

Provides question-answering capabilities for Malaysian Takaful documents and Islamic finance principles reference.

⚠️ **CURRENT STATUS: PLACEHOLDER IMPLEMENTATION** ⚠️
This skill provides the framework for Takaful document Q&A but requires additional development for production use.

## TODO: Implementation Required

- [ ] PDF text extraction for Takaful documents
- [ ] Question-answering logic implementation
- [ ] Islamic finance terminology database
- [ ] Shariah compliance reference framework
- [ ] Claims form field extraction
- [ ] Policy term identification
- [ ] Takaful product type classification

## Current Capabilities (Placeholder)

- Framework for document Q&A structure
- Islamic finance reference documentation
- Document analysis workflow
- Information extraction templates

## Supported Document Types

| Document Type | Capabilities | Limitations |
|---------------|--------------|-------------|
| Takaful Policy | Term extraction, coverage details | No binding interpretations |
| Claims Forms | Field identification, completion guidance | No claims processing |
| Product Disclosure | Feature comparison, term explanation | No product recommendations |
| Certificate of Takaful | Basic info extraction | No validity verification |

## Question Categories

### Policy Information
- Coverage terms and conditions
- Contribution amounts and schedules
- Beneficiary information
- Exclusions and limitations

### Claims Processing
- Required documentation
- Claim submission procedures
- Settlement timeframes
- Dispute resolution process

### Islamic Finance Principles
- Shariah compliance explanations
- Takaful vs conventional insurance
- Profit-sharing mechanisms
- Shariah governance structure

## Output Format

```json
{
  "question": "What is the coverage amount for medical benefits?",
  "answer": "Based on the uploaded policy document, the medical benefit coverage is RM 100,000 per year.",
  "source_reference": "Page 15, Section 3.2 of policy document",
  "confidence": "high|medium|low",
  "disclaimer": "This information is extracted from the provided document and requires verification. Consult the official policy for binding terms."
}
```

## Important Limitations

- ❌ No financial advice or recommendations
- ❌ No binding policy interpretations
- ❌ No claims processing or approval
- ❌ No Shariah compliance certification
- ✅ Information extraction only
- ✅ Reference guidance only
- ✅ General principle explanation

## Shariah Compliance Disclaimer

All outputs must include:
- This is not a Shariah compliance certification
- Consult qualified Shariah advisors for compliance matters
- Refer to official Shariah board rulings
- Islamic finance principles may vary by institution

⚠️ **HUMAN REVIEW REQUIRED** ⚠️
All document interpretations and Islamic finance guidance must be verified by qualified professionals.
This system provides information assistance only and does not replace expert advice.