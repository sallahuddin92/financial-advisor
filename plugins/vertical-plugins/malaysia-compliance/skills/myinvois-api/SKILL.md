---
name: myinvois-api
description: LHDN MyInvois API integration for e-Invoice validation. Currently supports sandbox testing and manual validation workflows.
---

# LHDN MyInvois API Integration

Provides access to LHDN MyInvois for e-Invoice validation and compliance checking.

⚠️ **CURRENT STATUS: PLACEHOLDER IMPLEMENTATION** ⚠️
This skill provides the framework for MyInvois integration but requires additional development for production use.

## TODO: Implementation Required

- [ ] MyInvois sandbox API integration
- [ ] Production API access configuration
- [ ] Authentication and security implementation
- [ ] Error handling and rate limiting
- [ ] Response parsing and validation
- [ ] Compliance rule implementation

## Current Capabilities (Placeholder)

- Framework for API integration structure
- Manual validation workflow documentation
- Compliance requirement references
- Test fixture support

## Manual Validation Workflow

Until API integration is complete, use this manual process:

1. Collect invoice details from user uploads
2. Document required fields for MyInvois compliance
3. Generate checklist for manual validation
4. Provide guidance for LHDN portal submission

## Required Fields for e-Invoice

Based on LHDN MyInvois requirements:
- Invoice number
- Date and time
- Supplier and customer details
- Item descriptions and quantities
- Tax amounts and codes
- Total amounts

## Output Format

All outputs include:
- Compliance status (with human review flags)
- Missing or invalid fields
- Recommendations for correction
- Links to official LHDN resources

⚠️ **HUMAN REVIEW REQUIRED** ⚠️
All compliance determinations must be verified against current LHDN requirements.
This system provides assistance only and does not guarantee compliance.