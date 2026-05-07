# Implementation TODO List

## Phase 1: Foundation (Current)

### Completed ✅
- [x] Create folder structure for Malaysia agents
- [x] Copy and rename agent manifests
- [x] Create Malaysia-adapted agent prompts
- [x] Create placeholder skills with TODO sections
- [x] Add guardrails and disclaimers

### In Progress 🔄
- [ ] Create sample test fixtures
- [ ] Add README documentation
- [ ] Create implementation status tracking

## Phase 2: Core Skills Implementation

### Bank Statement Parser
- [ ] Maybank CSV format implementation
- [ ] CIMB CSV format implementation
- [ ] Public Bank CSV format implementation
- [ ] RHB CSV format implementation
- [ ] Hong Leong Bank CSV format implementation
- [ ] XLSX format support
- [ ] Data validation and error handling

### MyInvois API Integration
- [ ] Sandbox API connection setup
- [ ] Authentication implementation
- [ ] Request/response handling
- [ ] Error handling and rate limiting
- [ ] Production API migration path

### SST Compliance
- [ ] Current SST rate implementation
- [ ] e-Invoice field validation
- [ ] Tax code mapping
- [ ] Calculation verification
- [ ] Exception handling

### Document Parsing
- [ ] SSM Form 24 parser
- [ ] SSM Form 49 parser
- [ ] Business certificate parser
- [ ] OCR integration for scanned docs
- [ ] Data validation logic

## Phase 3: Integration & Testing

### Test Cases
- [ ] Bank statement import tests
- [ ] Invoice matching tests
- [ ] KYC document processing tests
- [ ] Takaful document Q&A tests
- [ ] Compliance checklist tests

### Integration
- [ ] Agent-skill integration testing
- [ ] End-to-end workflow validation
- [ ] Error handling verification
- [ ] Performance testing

## Phase 4: Production Readiness

### Security & Compliance
- [ ] Data protection implementation
- [ ] Audit logging
- [ ] Access controls
- [ ] Compliance validation

### Documentation
- [ ] User guides
- [ ] API documentation
- [ ] Deployment guides
- [ ] Troubleshooting guides

## Future Enhancements

### Optional Integrations
- [ ] SSM API integration (when available)
- [ ] Additional bank formats
- [ ] Enhanced OCR capabilities
- [ ] Real-time compliance checking

### Advanced Features
- [ ] Machine learning for document classification
- [ ] Automated anomaly detection
- [ ] Advanced reporting dashboards
- [ ] Multi-language support

## Important Notes

- All implementations must include "HUMAN REVIEW REQUIRED" disclaimers
- No automated decision-making or approvals
- Focus on assistance and verification workflows
- Prioritize manual verification over automation
- Maintain compliance with Malaysian regulations