import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.simulation.fake_incidents import FAKE_INCIDENTS
from backend.agents.rca_agent import analyze_incident


def run_test():

    incident = FAKE_INCIDENTS[0]

    print("\n")
    print("=" * 80)
    print("TESTING RCA AGENT")
    print("=" * 80)

    print(f"\nIncident: {incident['title']}")
    print(f"Service: {incident['service']}")
    print(f"Severity: {incident['severity']}")

    print("\nRunning AI Root Cause Analysis...\n")

    response = analyze_incident(incident)

    print(response)

    print("\n")
    print("=" * 80)
    print("EXPECTED ROOT CAUSE")
    print("=" * 80)

    print(incident["expected_root_cause"])

    print("\n")
    print("=" * 80)
    print("EXPECTED FIX")
    print("=" * 80)

    print(incident["expected_fix"])


if __name__ == "__main__":
    run_test()
