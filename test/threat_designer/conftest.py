"""Threat-designer package tests: PYTHONPATH naar backend/threat_designer."""

import os
import sys
from pathlib import Path

# Minimal env so ``config.ThreatModelingConfig()`` loads when tests import ``workflow_threats``.
os.environ.setdefault("AGENT_STATE_TABLE", "test-agent-state-table")

_TD = Path(__file__).resolve().parent.parent.parent / "backend" / "threat_designer"
if str(_TD) not in sys.path:
    sys.path.insert(0, str(_TD))
