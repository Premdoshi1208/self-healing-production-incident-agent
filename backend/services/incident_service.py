from backend.simulation.fake_incidents import FAKE_INCIDENTS


def get_all_fake_incidents():
    return FAKE_INCIDENTS


def get_incident_by_id(incident_id: int):
    for incident in FAKE_INCIDENTS:
        if incident["id"] == incident_id:
            return incident

    return None