from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.storage.approval_store import (
    get_pending_approvals,
    load_approvals,
    set_approval_status
)


router = APIRouter()


class ApprovalRequest(BaseModel):
    reviewer: Optional[str] = "human-reviewer"
    comment: Optional[str] = ""


@router.get("/approvals")
def get_approvals():
    approvals = load_approvals()

    return {
        "total_approvals": len(approvals),
        "approvals": approvals
    }


@router.get("/approvals/pending")
def get_pending():
    approvals = get_pending_approvals()

    return {
        "total_pending": len(approvals),
        "approvals": approvals
    }


def _approval_request_or_default(request):
    return request or ApprovalRequest()


@router.post("/approvals/{run_id}/approve-staging")
def approve_staging(run_id: str, request: Optional[ApprovalRequest] = None):
    request = _approval_request_or_default(request)
    approval = set_approval_status(
        run_id,
        "approved_staging",
        reviewer=request.reviewer or "human-reviewer",
        comment=request.comment or "Approved for staging."
    )

    return {
        "message": "Run approved for staging.",
        "approval": approval
    }


@router.post("/approvals/{run_id}/reject")
def reject_patch(run_id: str, request: Optional[ApprovalRequest] = None):
    request = _approval_request_or_default(request)
    approval = set_approval_status(
        run_id,
        "rejected",
        reviewer=request.reviewer or "human-reviewer",
        comment=request.comment or "Patch rejected."
    )

    return {
        "message": "Run rejected.",
        "approval": approval
    }


@router.post("/approvals/{run_id}/approve-production")
def approve_production(run_id: str, request: Optional[ApprovalRequest] = None):
    request = _approval_request_or_default(request)
    approval = set_approval_status(
        run_id,
        "approved_production",
        reviewer=request.reviewer or "human-reviewer",
        comment=request.comment or "Human approval granted for production."
    )

    return {
        "message": "Human approval recorded for production. The LLM never grants production automatically.",
        "approval": approval
    }
