from fastapi import APIRouter

from backend.simulation.fake_incidents import (
    FAKE_INCIDENTS
)

from backend.workflows.incident_workflow import (
    run_incident_workflow
)

router = APIRouter()


@router.get("/incidents")
def get_all_incidents():

    return {
        "total_incidents": len(FAKE_INCIDENTS),
        "incidents": FAKE_INCIDENTS
    }


@router.post("/incidents/run/{incident_id}")
def run_incident(incident_id: int):

    incident = next(
        (
            incident
            for incident in FAKE_INCIDENTS
            if incident["id"] == incident_id
        ),
        None
    )

    if not incident:
        return {
            "error": "Incident not found"
        }

    workflow_result = run_incident_workflow(
        incident
    )

    return workflow_result