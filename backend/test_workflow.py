import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.simulation.fake_incidents import FAKE_INCIDENTS
from backend.workflows.incident_workflow import run_incident_workflow


def test_workflow():

    incident = FAKE_INCIDENTS[0]

    result = run_incident_workflow(incident)

    print("\n")
    print("=" * 80)
    print("FINAL WORKFLOW RESULT")
    print("=" * 80)

    print(result)


if __name__ == "__main__":
    test_workflow()
