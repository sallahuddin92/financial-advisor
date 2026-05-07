# Malaysia FSI Adaptation - Financial Services Agents

⚠️ **PHASE 1: FOUNDATION IMPLEMENTATION** ⚠️

This repository contains the foundation implementation of Malaysian Financial Services agents based on Anthropic's Claude for Financial Services reference architecture.

## 🚨 Important Disclaimers

### Current Status: PLACEHOLDER FRAMEWORK
- ✅ **Framework Created**: Agent and skill structures are in place
- ❌ **No Live Integrations**: All APIs are placeholder implementations
- ❌ **No Production Features**: No real-time data or automated decisions
- ✅ **Manual Workflows**: Focus on document upload and manual verification
- ✅ **Human Review Required**: All outputs require human verification

### What This Is NOT
- ❌ Fully functional production system
- ❌ Real-time government database integration
- ❌ Automated compliance checking
- ❌ Financial advice or recommendations
- ❌ Complete regulatory compliance solution

### What This IS
- ✅ Foundation framework for Malaysian financial workflows
- ✅ Manual document processing assistance
- ✅ Compliance checklist generation
- ✅ Reference information for Malaysian regulations
- ✅ Template for future development

## Offline Reconciliation MVP (Current)

- ✅ Implemented real parsing format: **Maybank CSV only**
- ✅ Offline invoice matching, reconciliation summaries, and JSON/CSV/Markdown report outputs
- ✅ Unified CLI entrypoint: `python3 -m malaysia_fsi.bank_statement.cli`
- ✅ Receipt JSON/manual ingestion and rule-based category engine (`malaysia_fsi.receipts`)
- 🚫 No MyInvois submission
- 🚫 No SSM/JPN/BNM verification
- 🚫 No live bank/government/credit bureau/market data API integrations
- ⚠️ **HUMAN REVIEW REQUIRED** for every output and decision

### Supported Receipt Workflows

- JSON/manual receipt input
- Rule-based categorization (transparent keyword rules)
- Batch categorization with duplicate candidate detection
- Monthly SME expense summary generation
- Monthly exports: JSON, CSV, Markdown
- Human-review-required warnings for all categorized outputs

### Quick Commands

```bash
# Parse statement
python3 -m malaysia_fsi.bank_statement.cli parse test-fixtures/sample-data/maybank-valid.csv --json

# Match invoices and export markdown report
python3 -m malaysia_fsi.bank_statement.cli match \
  test-fixtures/sample-data/maybank-valid.csv \
  test-fixtures/sample-data/invoices-exact-match \
  --format md \
  --output /tmp/reconciliation-report.md
```

## 🏗️ Architecture Overview

```
plugins/
├── agent-plugins/
│   ├── my-sme-reconciler/     # Bank statement + invoice reconciliation
│   ├── my-kyc-screener/       # Malaysian KYC document processing
│   └── my-takaful-assistant/  # Islamic finance document Q&A
└── vertical-plugins/
    └── malaysia-compliance/   # Core Malaysian compliance skills
        ├── myinvois-api/      # LHDN e-Invoice integration framework
        ├── bank-statement-parser/ # Malaysian bank format parser
        ├── sst-checklist/     # SST compliance framework
        ├── ssm-doc-parse/     # SSM document processing framework
        ├── my-kyc-checklist/  # BNM AML/CFT framework
        └── takaful-doc-qa/    # Islamic finance Q&A framework
```

## 📋 Agent Descriptions

### MY-SME Reconciler
**Purpose**: Assist with Malaysian SME bank statement and invoice reconciliation
**Current Capabilities**:
- Framework for bank statement processing
- Manual invoice matching workflow
- LHDN e-Invoice compliance reference
- SST/GST checklist generation

**Limitations**:
- No real-time bank feeds
- No automated matching
- Manual document upload only

### MY-KYC Screener
**Purpose**: Support Malaysian KYC document processing and verification
**Current Capabilities**:
- Framework for Malaysian document types
- BNM AML/CFT checklist generation
- Risk factor identification
- Manual verification workflows

**Limitations**:
- No live government database access
- No automated PEP/sanctions screening
- Manual document processing only

### MY-Takaful Assistant
**Purpose**: Provide Q&A assistance for Malaysian Takaful documents
**Current Capabilities**:
- Framework for Islamic finance document Q&A
- Information extraction from uploaded documents
- Shariah compliance reference information
- Claims form assistance

**Limitations**:
- No binding interpretations
- No Shariah compliance certification
- Information extraction only

## 🛠️ Skills Framework

### Core Compliance Skills (Placeholder)
- **myinvois-api**: LHDN MyInvois integration structure
- **bank-statement-parser**: Malaysian bank format support
- **sst-checklist**: SST/e-Invoice compliance framework
- **ssm-doc-parse**: SSM document processing framework
- **my-kyc-checklist**: BNM AML/CFT guidelines framework
- **takaful-doc-qa**: Islamic finance Q&A framework

### What Skills Provide
- ✅ Framework structure and workflows
- ✅ Manual verification procedures
- ✅ Compliance requirement references
- ✅ Document processing templates
- ✅ Checklist generation

### What Skills DON'T Provide
- ❌ Live API integrations
- ❌ Real-time data processing
- ❌ Automated decisions
- ❌ Production authentication

## 🧪 Test Fixtures

Sample data files are provided in `/test-fixtures/`:

### Sample Data
- `sample-maybank-statement.csv`: Sample bank statement format
- `sample-invoice.json`: Sample invoice structure

### Sample Documents
- `sample-ssm-form24.txt`: Sample SSM Form 24 structure
- `sample-takaful-policy.txt`: Sample Takaful policy structure

⚠️ All sample data is fictional and for testing only

## 🚦 Getting Started

### Prerequisites
- Access to Claude Code or Claude Cowork
- Understanding of Malaysian financial regulations
- Manual verification processes

### Installation (Framework Only)
```bash
# Add marketplace (when available)
claude plugin marketplace add anthropics/claude-for-financial-services

# Install Malaysia compliance skills (framework only)
claude plugin install malaysia-compliance@claude-for-financial-services

# Install Malaysia agents (framework only)
claude plugin install my-sme-reconciler@claude-for-financial-services
claude plugin install my-kyc-screener@claude-for-financial-services
claude plugin install my-takaful-assistant@claude-for-financial-services
```

### Usage Guidelines
1. **Upload Documents**: Use manual document upload features
2. **Review Outputs**: All outputs require human verification
3. **Check Compliance**: Verify against current Malaysian regulations
4. **Manual Verification**: Cross-check all information with official sources
5. **Professional Review**: Consult qualified professionals for all decisions

## 📖 Documentation

- `TODO.md`: Implementation roadmap and future features
- `IMPLEMENTATION_STATUS.md`: Current status and limitations
- `MVP_SCOPE.md`: Detailed scope definition and boundaries

## ⚠️ Critical Limitations

### No Live Integrations
- No real-time government API access
- No live bank feeds
- No automated screening databases
- No production system connections

### Manual Processing Only
- Document upload required
- Manual verification necessary
- No automated workflows
- Human review mandatory

### Reference Only
- Information provided for assistance only
- No binding interpretations
- No compliance guarantees
- Professional verification required

## 🔒 Security & Compliance

### Data Handling
- All documents treated as untrusted
- No automatic data transmission
- Manual verification workflows
- Local processing only

### Compliance Notes
- All outputs marked "HUMAN REVIEW REQUIRED"
- No automated compliance determinations
- Current regulation verification required
- Professional oversight mandatory

## 🚀 Future Development

See `TODO.md` for planned implementation phases:
1. **Phase 2**: Basic document parsing implementation
2. **Phase 3**: Enhanced compliance checking
3. **Phase 4**: Optional live integrations (when available)

## 📞 Support & Contact

This is a foundation framework. For:
- **Implementation questions**: Review documentation
- **Compliance concerns**: Consult qualified professionals
- **Technical issues**: Check framework limitations
- **Feature requests**: Review TODO.md for roadmap

## 📄 License

This adaptation maintains the original Apache License 2.0 from the source repository.

---

**Remember**: This is a framework for assistance only. All financial, legal, and compliance decisions require qualified professional review and verification against current Malaysian regulations.
