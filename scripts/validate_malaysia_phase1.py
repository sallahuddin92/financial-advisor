#!/usr/bin/env python3
"""
Phase 1 Structure Validation Script
Validates the Malaysia FSI adaptation foundation implementation
"""

import json
import sys
import yaml
from pathlib import Path

def check_json_valid(filepath):
    """Check if a JSON file is valid"""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, FileNotFoundError):
        return False

def check_yaml_frontmatter(filepath):
    """Check if markdown file has valid YAML frontmatter"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    yaml_content = parts[1]
                    yaml.safe_load(yaml_content)
                    return True
        return False
    except (yaml.YAMLError, FileNotFoundError):
        return False

def check_disclaimer(filepath):
    """Check if file contains required disclaimer"""
    try:
        with open(filepath, 'r') as f:
            content = f.read().upper()
            return ('HUMAN REVIEW REQUIRED' in content or
                    'HUMAN REVIEW REQUIRED' in content or
                    'HUMAN VERIFICATION REQUIRED' in content)
    except FileNotFoundError:
        return False

def check_no_false_claims(filepath):
    """Check that file doesn't claim production integration is complete"""
    try:
        with open(filepath, 'r') as f:
            content = f.read().upper()
            false_claims = [
                'FULLY INTEGRATED',
                'PRODUCTION READY',
                'LIVE API',
                'REAL-TIME',
                'AUTOMATED APPROVAL',
                'COMPLETE INTEGRATION'
            ]
            for claim in false_claims:
                if claim in content:
                    # Allow if it's in a TODO or negation context
                    if 'TODO' in content or 'NOT' in content or 'DISABLED' in content:
                        continue
                    return False
        return True
    except FileNotFoundError:
        return False

def main():
    """Main validation function"""
    base_path = Path(__file__).resolve().parent.parent
    checks = []

    # 1. Check all plugin.json files are valid JSON
    plugin_jsons = [
        'plugins/agent-plugins/my-sme-reconciler/.claude-plugin/plugin.json',
        'plugins/agent-plugins/my-kyc-screener/.claude-plugin/plugin.json',
        'plugins/agent-plugins/my-takaful-assistant/.claude-plugin/plugin.json',
        'plugins/vertical-plugins/malaysia-compliance/.claude-plugin/plugin.json'
    ]

    for plugin_json in plugin_jsons:
        filepath = base_path / plugin_json
        if check_json_valid(filepath):
            checks.append(f"PASS: {plugin_json} is valid JSON")
        else:
            checks.append(f"FAIL: {plugin_json} is not valid JSON")
            return False, checks

    # 2. Check all expected agent markdown files exist
    agent_files = [
        'plugins/agent-plugins/my-sme-reconciler/agents/my-sme-reconciler.md',
        'plugins/agent-plugins/my-kyc-screener/agents/my-kyc-screener.md',
        'plugins/agent-plugins/my-takaful-assistant/agents/my-takaful-assistant.md'
    ]

    for agent_file in agent_files:
        filepath = base_path / agent_file
        if filepath.exists():
            checks.append(f"PASS: {agent_file} exists")
        else:
            checks.append(f"FAIL: {agent_file} does not exist")
            return False, checks

    # 3. Check all expected skill SKILL.md files exist
    skill_files = [
        'plugins/vertical-plugins/malaysia-compliance/skills/myinvois-api/SKILL.md',
        'plugins/vertical-plugins/malaysia-compliance/skills/bank-statement-parser/SKILL.md',
        'plugins/vertical-plugins/malaysia-compliance/skills/sst-checklist/SKILL.md',
        'plugins/vertical-plugins/malaysia-compliance/skills/ssm-doc-parse/SKILL.md',
        'plugins/vertical-plugins/malaysia-compliance/skills/my-kyc-checklist/SKILL.md',
        'plugins/vertical-plugins/malaysia-compliance/skills/takaful-doc-qa/SKILL.md'
    ]

    for skill_file in skill_files:
        filepath = base_path / skill_file
        if filepath.exists():
            checks.append(f"PASS: {skill_file} exists")
        else:
            checks.append(f"FAIL: {skill_file} does not exist")
            return False, checks

    # 4. Check YAML frontmatter in agent/skill files is parseable
    all_md_files = agent_files + skill_files
    for md_file in all_md_files:
        filepath = base_path / md_file
        if check_yaml_frontmatter(filepath):
            checks.append(f"PASS: {md_file} has valid YAML frontmatter")
        else:
            checks.append(f"FAIL: {md_file} does not have valid YAML frontmatter")
            return False, checks

    # 5. Check no placeholder accidentally claims production integration is complete
    for md_file in all_md_files:
        filepath = base_path / md_file
        if check_no_false_claims(filepath):
            checks.append(f"PASS: {md_file} has no false production claims")
        else:
            checks.append(f"FAIL: {md_file} contains false production claims")
            return False, checks

    # 6. Check every agent/skill includes disclaimer
    for md_file in all_md_files:
        filepath = base_path / md_file
        if check_disclaimer(filepath):
            checks.append(f"PASS: {md_file} includes required disclaimer")
        else:
            checks.append(f"FAIL: {md_file} missing required disclaimer")
            return False, checks

    # 7. Check test fixture files exist
    test_files = [
        'test-fixtures/sample-data/sample-maybank-statement.csv',
        'test-fixtures/sample-data/sample-invoice.json',
        'test-fixtures/documents/sample-ssm-form24.txt',
        'test-fixtures/documents/sample-takaful-policy.txt'
    ]

    for test_file in test_files:
        filepath = base_path / test_file
        if filepath.exists():
            checks.append(f"PASS: {test_file} exists")
        else:
            checks.append(f"FAIL: {test_file} does not exist")
            return False, checks

    # 8. Check documentation files exist
    doc_files = [
        'README-MY.md',
        'MVP_SCOPE.md',
        'TODO.md',
        'IMPLEMENTATION_STATUS.md',
        'PHASE1_SUMMARY.md'
    ]

    for doc_file in doc_files:
        filepath = base_path / doc_file
        if filepath.exists():
            checks.append(f"PASS: {doc_file} exists")
        else:
            checks.append(f"FAIL: {doc_file} does not exist")
            return False, checks

    return True, checks

if __name__ == '__main__':
    success, results = main()

    print("\n=== Phase 1 Structure Validation Results ===\n")

    for result in results:
        print(result)

    print(f"\n=== Summary ===")
    passed = sum(1 for r in results if r.startswith('PASS'))
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if success:
        print("\n✅ ALL CHECKS PASSED - Phase 1 structure is valid!")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION FAILED - Please fix the issues above")
        sys.exit(1)
