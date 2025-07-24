#!/usr/bin/env python3
"""
Security Review Script for RAG System

This script performs a security review of documents before they are ingested
into the RAG system to identify potentially sensitive content.
"""
import os
import sys
import re
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_sensitive_patterns() -> Dict[str, List[str]]:
    """Load patterns for detecting sensitive content."""
    return {
        'api_keys': [
            r'[a-zA-Z0-9]{32,}',  # Long alphanumeric strings
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI-style keys
            r'AIza[a-zA-Z0-9]{35}',  # Google API keys
            r'[a-zA-Z0-9]{40}',  # GitHub tokens
        ],
        'passwords': [
            r'password\s*[:=]\s*[\'"][^\'"]+[\'"]',
            r'passwd\s*[:=]\s*[\'"][^\'"]+[\'"]',
            r'pwd\s*[:=]\s*[\'"][^\'"]+[\'"]',
        ],
        'emails': [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ],
        'phone_numbers': [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US phone numbers
            r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
        ],
        'credit_cards': [
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Basic CC pattern
        ],
        'ip_addresses': [
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        ],
        'database_connections': [
            r'postgresql://[^\s]+',
            r'mysql://[^\s]+',
            r'mongodb://[^\s]+',
            r'redis://[^\s]+',
        ],
        'sensitive_keywords': [
            r'\b(secret|password|key|token|credential|private|confidential|internal)\b',
            r'\b(admin|root|superuser)\b',
            r'\b(ssn|social\s+security)\b',
            r'\b(credit\s+card|cc\s+number)\b',
        ]
    }

def scan_file_content(file_path: Path, patterns: Dict[str, List[str]]) -> Dict[str, Any]:
    """Scan a single file for sensitive content."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        findings = {
            'file_path': str(file_path),
            'file_size': len(content),
            'issues': {},
            'risk_level': 'low'
        }
        
        total_issues = 0
        
        for category, pattern_list in patterns.items():
            category_findings = []
            
            for pattern in pattern_list:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Mask the actual content for security
                    matched_text = match.group(0)
                    if len(matched_text) > 10:
                        masked_text = matched_text[:4] + '*' * (len(matched_text) - 8) + matched_text[-4:]
                    else:
                        masked_text = '*' * len(matched_text)
                    
                    category_findings.append({
                        'line': content[:match.start()].count('\n') + 1,
                        'position': match.start(),
                        'masked_content': masked_text,
                        'pattern': pattern
                    })
            
            if category_findings:
                findings['issues'][category] = category_findings
                total_issues += len(category_findings)
        
        # Determine risk level
        if total_issues == 0:
            findings['risk_level'] = 'low'
        elif total_issues <= 3:
            findings['risk_level'] = 'medium'
        else:
            findings['risk_level'] = 'high'
        
        findings['total_issues'] = total_issues
        
        return findings
        
    except Exception as e:
        return {
            'file_path': str(file_path),
            'error': str(e),
            'risk_level': 'unknown'
        }

def scan_directory(directory_path: Path, patterns: Dict[str, List[str]]) -> Dict[str, Any]:
    """Scan a directory for sensitive content."""
    print(f"🔍 Scanning directory: {directory_path}")
    
    results = {
        'directory': str(directory_path),
        'files_scanned': 0,
        'files_with_issues': 0,
        'total_issues': 0,
        'risk_level': 'low',
        'findings': []
    }
    
    if not directory_path.exists():
        return {
            'directory': str(directory_path),
            'error': 'Directory does not exist'
        }
    
    # Supported file extensions
    supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.doc', '.rtf'}
    
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            results['files_scanned'] += 1
            
            file_findings = scan_file_content(file_path, patterns)
            results['findings'].append(file_findings)
            
            if file_findings.get('total_issues', 0) > 0:
                results['files_with_issues'] += 1
                results['total_issues'] += file_findings['total_issues']
    
    # Determine overall risk level
    if results['total_issues'] == 0:
        results['risk_level'] = 'low'
    elif results['total_issues'] <= 10:
        results['risk_level'] = 'medium'
    else:
        results['risk_level'] = 'high'
    
    return results

def generate_security_report(scan_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a comprehensive security report."""
    print("📋 Generating security report...")
    
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'overall_risk_level': 'low',
        'summary': {
            'directories_scanned': 0,
            'total_files_scanned': 0,
            'files_with_issues': 0,
            'total_issues_found': 0
        },
        'detailed_results': scan_results,
        'recommendations': []
    }
    
    # Aggregate results
    for result in scan_results.values():
        if isinstance(result, dict) and 'files_scanned' in result:
            report['summary']['directories_scanned'] += 1
            report['summary']['total_files_scanned'] += result.get('files_scanned', 0)
            report['summary']['files_with_issues'] += result.get('files_with_issues', 0)
            report['summary']['total_issues_found'] += result.get('total_issues', 0)
    
    # Determine overall risk level
    if report['summary']['total_issues_found'] == 0:
        report['overall_risk_level'] = 'low'
    elif report['summary']['total_issues_found'] <= 10:
        report['overall_risk_level'] = 'medium'
    else:
        report['overall_risk_level'] = 'high'
    
    # Generate recommendations
    if report['summary']['files_with_issues'] > 0:
        report['recommendations'].append(
            f"Review {report['summary']['files_with_issues']} files with potential sensitive content"
        )
    
    if report['overall_risk_level'] == 'high':
        report['recommendations'].append(
            "High risk level detected. Review all findings before RAG ingestion"
        )
    
    if report['summary']['total_issues_found'] > 0:
        report['recommendations'].append(
            "Consider implementing content filtering before ingestion"
        )
    
    return report

def print_security_report(report: Dict[str, Any]):
    """Print formatted security report."""
    print("\n" + "="*80)
    print("🔒 SECURITY REVIEW REPORT")
    print("="*80)
    print(f"Generated: {report['timestamp']}")
    print(f"Overall Risk Level: {report['overall_risk_level'].upper()}")
    print("="*80)
    
    # Summary
    summary = report['summary']
    print(f"\n📊 SUMMARY:")
    print(f"   Directories scanned: {summary['directories_scanned']}")
    print(f"   Total files scanned: {summary['total_files_scanned']}")
    print(f"   Files with issues: {summary['files_with_issues']}")
    print(f"   Total issues found: {summary['total_issues_found']}")
    
    # Detailed results
    print(f"\n🔍 DETAILED RESULTS:")
    for dir_path, result in report['detailed_results'].items():
        if isinstance(result, dict) and 'files_scanned' in result:
            print(f"\n   Directory: {result['directory']}")
            print(f"   Files scanned: {result['files_scanned']}")
            print(f"   Files with issues: {result['files_with_issues']}")
            print(f"   Risk level: {result['risk_level']}")
            
            # Show high-risk files
            high_risk_files = [f for f in result['findings'] if f.get('risk_level') == 'high']
            if high_risk_files:
                print(f"   ⚠️  High-risk files:")
                for file_finding in high_risk_files[:3]:  # Show first 3
                    print(f"      - {Path(file_finding['file_path']).name}")
    
    # Recommendations
    print(f"\n📋 RECOMMENDATIONS:")
    for recommendation in report['recommendations']:
        print(f"   • {recommendation}")
    
    if report['overall_risk_level'] == 'low':
        print(f"\n✅ Security review passed. Safe to proceed with RAG ingestion.")
    elif report['overall_risk_level'] == 'medium':
        print(f"\n⚠️  Medium risk detected. Review findings before proceeding.")
    else:
        print(f"\n❌ High risk detected. Address security issues before proceeding.")
    
    print("\n" + "="*80)

def save_security_report(report: Dict[str, Any], filename: str = "security_review_report.json"):
    """Save security report to file."""
    report_path = Path("logs") / filename
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Security report saved to: {report_path}")

def main():
    """Main security review function."""
    print("🔒 Starting Security Review for RAG System...")
    print("This will scan documents for potentially sensitive content.\n")
    
    try:
        # Load sensitive patterns
        patterns = load_sensitive_patterns()
        
        # Scan guidelines directory
        guidelines_path = Path("../docs/guidelines")
        scan_results = {}
        
        if guidelines_path.exists():
            scan_results['guidelines'] = scan_directory(guidelines_path, patterns)
        
        # Generate report
        report = generate_security_report(scan_results)
        
        # Print report
        print_security_report(report)
        
        # Save report
        save_security_report(report)
        
        # Return exit code based on risk level
        if report['overall_risk_level'] == 'low':
            print("\n✅ Security review completed. Safe to proceed.")
            return 0
        elif report['overall_risk_level'] == 'medium':
            print("\n⚠️  Security review completed. Review findings before proceeding.")
            return 1
        else:
            print("\n❌ Security review completed. Address issues before proceeding.")
            return 2
            
    except Exception as e:
        print(f"\n❌ Security review failed: {e}")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit(main()) 