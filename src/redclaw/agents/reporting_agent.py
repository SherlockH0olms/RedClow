"""
RedClaw - Reporting Agent
Evidence collection, timeline construction, report generation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from ..core.llm_client import RedClawLLM, Message


@dataclass
class Evidence:
    """Collected evidence"""
    phase: str
    title: str
    description: str
    raw_data: str
    screenshot: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Finding:
    """Security finding"""
    severity: str  # critical, high, medium, low, info
    title: str
    description: str
    evidence: List[Evidence]
    remediation: str
    cvss: Optional[float] = None
    cve: Optional[str] = None
    owasp: Optional[str] = None


class ReportingAgent:
    """
    Reporting Agent - Documentation and reporting
    
    Capabilities:
    - Evidence collection
    - Timeline construction
    - Finding categorization
    - Report generation (Markdown, JSON, HTML)
    - Compliance mapping (OWASP, PTES)
    """
    
    def __init__(self, llm: RedClawLLM):
        self.llm = llm
        self.evidence: List[Evidence] = []
        self.findings: List[Finding] = []
        self.timeline: List[Dict] = []
        self.target: str = ""
        self.start_time: datetime = datetime.now()
    
    def set_target(self, target: str):
        """Set target for report"""
        self.target = target
        self.start_time = datetime.now()
    
    def add_evidence(
        self,
        phase: str,
        title: str,
        description: str,
        raw_data: str,
        screenshot: str = None
    ):
        """Add evidence"""
        ev = Evidence(
            phase=phase,
            title=title,
            description=description,
            raw_data=raw_data,
            screenshot=screenshot
        )
        self.evidence.append(ev)
        
        self.timeline.append({
            "time": datetime.now().isoformat(),
            "phase": phase,
            "action": title
        })
    
    def add_finding(
        self,
        severity: str,
        title: str,
        description: str,
        evidence_titles: List[str],
        remediation: str,
        cvss: float = None,
        cve: str = None
    ):
        """Add security finding"""
        related_evidence = [
            e for e in self.evidence
            if e.title in evidence_titles
        ]
        
        finding = Finding(
            severity=severity,
            title=title,
            description=description,
            evidence=related_evidence,
            remediation=remediation,
            cvss=cvss,
            cve=cve
        )
        self.findings.append(finding)
    
    def categorize_findings(self) -> Dict[str, List[Finding]]:
        """Categorize findings by severity"""
        categories = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }
        
        for finding in self.findings:
            if finding.severity in categories:
                categories[finding.severity].append(finding)
        
        return categories
    
    async def generate_executive_summary(self) -> str:
        """Generate executive summary using LLM"""
        categories = self.categorize_findings()
        
        summary_data = f"""
Target: {self.target}
Duration: {datetime.now() - self.start_time}
Total Findings: {len(self.findings)}
- Critical: {len(categories['critical'])}
- High: {len(categories['high'])}
- Medium: {len(categories['medium'])}
- Low: {len(categories['low'])}
- Info: {len(categories['info'])}

Key findings:
"""
        for finding in self.findings[:5]:
            summary_data += f"\n- [{finding.severity.upper()}] {finding.title}"
        
        messages = [
            Message(role="system", content="""Generate a professional executive summary 
for a penetration test report. Be concise but comprehensive. 
Include overall risk assessment and key recommendations."""),
            Message(role="user", content=summary_data)
        ]
        
        response = self.llm.chat(messages, max_tokens=800)
        return response.content
    
    def generate_markdown_report(self) -> str:
        """Generate full Markdown report"""
        categories = self.categorize_findings()
        
        report = f"""# Penetration Test Report

## Target Information
- **Target:** {self.target}
- **Test Date:** {self.start_time.strftime('%Y-%m-%d')}
- **Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Executive Summary

This penetration test identified **{len(self.findings)}** security findings:

| Severity | Count |
|----------|-------|
| Critical | {len(categories['critical'])} |
| High | {len(categories['high'])} |
| Medium | {len(categories['medium'])} |
| Low | {len(categories['low'])} |
| Informational | {len(categories['info'])} |

---

## Findings

"""
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            if categories[severity]:
                report += f"### {severity.upper()} Severity\n\n"
                
                for i, finding in enumerate(categories[severity], 1):
                    report += f"""#### {i}. {finding.title}

**Severity:** {finding.severity.upper()}
{f"**CVE:** {finding.cve}" if finding.cve else ""}
{f"**CVSS:** {finding.cvss}" if finding.cvss else ""}

**Description:**
{finding.description}

**Evidence:**
"""
                    for ev in finding.evidence:
                        report += f"""
```
{ev.raw_data[:1000]}
```
"""
                    report += f"""
**Remediation:**
{finding.remediation}

---

"""
        
        # Timeline
        report += """## Attack Timeline

| Time | Phase | Action |
|------|-------|--------|
"""
        for event in self.timeline:
            report += f"| {event['time']} | {event['phase']} | {event['action']} |\n"
        
        # Methodology
        report += """

---

## Methodology

This penetration test followed the PTES (Penetration Testing Execution Standard) methodology:

1. **Pre-engagement Interactions** - Scope definition and authorization
2. **Intelligence Gathering** - OSINT and reconnaissance
3. **Threat Modeling** - Attack surface analysis
4. **Vulnerability Analysis** - Service and vulnerability scanning
5. **Exploitation** - Vulnerability verification and exploitation
6. **Post-Exploitation** - Privilege escalation and lateral movement
7. **Reporting** - Documentation and remediation recommendations

---

## Disclaimer

This penetration test was conducted under authorized conditions. All findings should be 
remediated in order of severity. This report is confidential and should be handled 
according to your organization's information security policies.

---

*Report generated by RedClaw Autonomous Penetration Testing System*
"""
        return report
    
    def generate_json_report(self) -> Dict:
        """Generate JSON report"""
        return {
            "target": self.target,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "findings": [
                {
                    "severity": f.severity,
                    "title": f.title,
                    "description": f.description,
                    "remediation": f.remediation,
                    "cvss": f.cvss,
                    "cve": f.cve
                }
                for f in self.findings
            ],
            "timeline": self.timeline,
            "summary": {
                "total_findings": len(self.findings),
                "by_severity": {
                    s: len([f for f in self.findings if f.severity == s])
                    for s in ['critical', 'high', 'medium', 'low', 'info']
                }
            }
        }
    
    def save_report(self, output_dir: str, format: str = "markdown") -> str:
        """Save report to file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == "markdown":
            filename = f"report_{timestamp}.md"
            content = self.generate_markdown_report()
            (output_path / filename).write_text(content)
        elif format == "json":
            filename = f"report_{timestamp}.json"
            content = self.generate_json_report()
            (output_path / filename).write_text(json.dumps(content, indent=2))
        
        return str(output_path / filename)
