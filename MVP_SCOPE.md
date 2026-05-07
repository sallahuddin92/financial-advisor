# Malaysia FSI Adaptation - MVP Scope Definition

## MVP Goals

Create a functional foundation for Malaysian financial services workflows that:
1. Provides document processing assistance (NOT automation)
2. Supports manual verification workflows
3. Includes comprehensive compliance disclaimers
4. Focuses on Malaysian regulatory requirements
5. Requires human review for all outputs

## In Scope ✅

### Core Workflows
- [x] **Document Upload & Processing**: Offline CSV + JSON handling for reconciliation workflows
- [x] **Bank Statement Import**: Manual upload and parsing for Maybank CSV
- [x] **Invoice Processing**: Manual upload and offline invoice matching/reporting
- [ ] **KYC Document Processing**: Manual upload and checklist generation
- [ ] **Takaful Document Q&A**: PDF analysis and information extraction
- [ ] **Compliance Checklists**: SST, e-Invoice, KYC verification templates

### Data Sources (Manual)
- [ ] **File Uploads**: User-provided documents and statements
- [ ] **Sample Data**: Test fixtures for development and validation
- [ ] **Reference Materials**: Malaysian compliance guidelines and requirements
- [ ] **Static Lists**: Malaysian bank formats, tax codes, document types

### Implemented Bank Coverage
- [x] **Maybank CSV**: Implemented
- [ ] **CIMB/Public Bank/RHB/Hong Leong**: Placeholder architecture only (disabled until anonymized fixtures are available)

### Output Types
- [ ] **Reconciliation Reports**: Bank vs invoice matching with variance flags
- [ ] **Compliance Checklists**: Itemized verification requirements
- [ ] **KYC Assessment Reports**: Risk factors and missing items
- [ ] **Document Extraction Summaries**: Key information from uploaded files
- [ ] **Exception Reports**: Items requiring human attention

## Out of Scope ❌

### Real-time Integrations
- ❌ Live government API access (SSM, LHDN, BNM)
- ❌ Real-time bank feeds or statement downloads
- ❌ Live screening databases (PEP, sanctions)
- ❌ Real-time market data feeds
- ❌ Live compliance checking systems

### Automated Decisions
- ❌ Automated approvals or rejections
- ❌ Risk rating without human review
- ❌ Compliance certification
- ❌ Financial advice or recommendations
- ❌ Shariah compliance determination

### Advanced Features
- ❌ Machine learning document classification
- ❌ Predictive analytics
- ❌ Automated anomaly detection
- ❌ Real-time monitoring
- ❌ Advanced reporting dashboards

### Production Systems
- ❌ Production API credentials
- ❌ Live database connections
- ❌ Real-time data processing
- ❌ Automated batch processing
- ❌ Integration with core banking systems

## Technical Boundaries

### What We Build
- ✅ Document parsing frameworks
- ✅ Data extraction utilities
- ✅ Compliance checklist generators
- ✅ Report formatting tools
- ✅ Offline reconciliation JSON/CSV/Markdown export
- ✅ User workflow guides
- ✅ Manual verification procedures

### What We Don't Build
- ❌ Production integrations
- ❌ Live data connections
- ❌ Automated workflows
- ❌ Real-time processing
- ❌ Production authentication

## Success Criteria

### MVP Success = ✅
- Framework supports manual document upload
- Checklists are generated for human review
- All outputs include "human review required" disclaimers
- Malaysian compliance requirements are referenced
- No false claims about automation or live data
- Clear documentation of limitations

### MVP Success ≠ ❌
- Fully automated processing
- Real-time integrations
- Production-ready deployments
- Complete regulatory compliance
- 100% accuracy in document processing

## Risk Management

### Technical Risks
- **Risk**: Over-promising automation capabilities
  **Mitigation**: Clear "placeholder" labeling and manual workflow emphasis

- **Risk**: False compliance claims
  **Mitigation**: Comprehensive disclaimers and human review requirements

- **Risk**: Integration complexity
  **Mitigation**: Start with manual processes, add automation gradually

### Compliance Risks
- **Risk**: Regulatory non-compliance
  **Mitigation**: Human review required for all outputs

- **Risk**: Outdated regulation references
  **Mitigation**: Clear documentation that users must verify against current regulations

- **Risk**: Misinterpretation of Islamic finance principles
  **Mitigation**: Reference only, no binding interpretations

## Implementation Approach

### Phase 1: Foundation (Current)
- ✅ Create agent and skill frameworks
- ✅ Add guardrails and disclaimers
- 🔄 Create sample test fixtures
- 🔄 Add comprehensive documentation

### Phase 2: Basic Functionality
- 🔄 Implement basic document parsing
- 🔄 Create sample data processing
- 🔄 Add manual verification workflows
- 🔄 Test with sample documents

### Phase 3: Enhanced Features
- 🔄 Add more bank formats
- 🔄 Enhance compliance checking
- 🔄 Improve document extraction
- 🔄 Add more test cases

### Phase 4: Optional Integrations
- 🔄 Consider live API integrations
- 🔄 Evaluate automation opportunities
- 🔄 Assess production readiness
- 🔄 Plan for scale

## Key Principles

1. **Transparency**: Clear about what is and isn't implemented
2. **Safety**: Human review required for all decisions
3. **Compliance**: Malaysian regulatory focus
4. **Gradual**: Build from manual to automated carefully
5. **Honest**: No false claims about capabilities

This MVP scope ensures we build something useful while being completely transparent about limitations and avoiding regulatory or compliance risks.
