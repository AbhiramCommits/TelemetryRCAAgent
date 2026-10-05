"""Report renderer for incidents as readable markdown."""

from telemetry_rca.schema import Incident


def render_incident_report(incident: Incident) -> str:
    """Render an incident as readable markdown with evidence trace."""
    md = f"""# Incident Report: {incident.id}

- **Entity:** `{incident.entity}`
- **Timestamp:** `{incident.ts}`
- **Anomaly Score:** `{incident.score:.2f}`
- **Resolution Latency:** `{incident.latency_ms:.2f} ms`

## Ranked Root-Cause Hypotheses (Top-3)
"""
    for idx, hyp in enumerate(incident.hypothesis[:3]):
        md += f"{idx + 1}. **{hyp.get('entity')}** (Confidence Score: `{hyp.get('score')}`)\n"
        md += f"   - *Reason:* {hyp.get('reason')}\n"

    md += "\n## Evidence Trace\n"
    for ev in incident.evidence:
        md += f"- **{ev.get('type')}:** `{ev}`\n"

    return md
