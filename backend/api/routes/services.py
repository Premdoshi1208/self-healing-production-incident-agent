from fastapi import APIRouter

from backend.services.service_status import get_service_statuses


router = APIRouter()


@router.get("/services/status")
def get_services_status():
    return get_service_statuses()
