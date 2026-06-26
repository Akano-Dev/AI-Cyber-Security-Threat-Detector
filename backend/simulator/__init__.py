"""
ACSTD synthetic traffic simulator — reusable modules.

This package generates *synthetic demo traffic* to exercise ACSTD's own
detector via its public /api/v1/analyze endpoint. The payloads are textbook
detection-test strings (the same kind already shipped in this repo), not
working exploits or malware. Nothing here attacks third-party systems.

Public API:
    from simulator import AnalyzeClient, Simulator, SCENARIOS

    client = AnalyzeClient("http://localhost:8000/api/v1")
    Simulator(client).run_scenario("sqli")
    Simulator(client).run_mixed(count=20)
"""
from .client import AnalyzeClient
from .scenarios import SCENARIOS, Event
from .runner import Simulator

__all__ = ["AnalyzeClient", "Simulator", "SCENARIOS", "Event"]
