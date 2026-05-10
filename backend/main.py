from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from backend.api.routes.incidents import router as incidents_router
from backend.api.routes.prometheus_webhook import router as prometheus_router
from backend.api.routes.memory import router as memory_router
from backend.api.routes.runs import router as runs_router
from backend.api.routes.approvals import router as approvals_router
from backend.api.routes.github import router as github_router
from backend.api.routes.qa import router as qa_router
from backend.api.routes.services import router as services_router
from backend.api.routes.codebase import router as codebase_router
from backend.api.routes.patches import router as patches_router

app = FastAPI(
    title="Self-Healing Production Incident Agent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
                "path": str(request.url.path)
            }
        }
    )


@app.get("/")
def root():
    return {
        "message": "Self-Healing Production Incident Agent API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


app.include_router(incidents_router, prefix="/api")
app.include_router(prometheus_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(runs_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(github_router, prefix="/api")
app.include_router(qa_router, prefix="/api")
app.include_router(services_router, prefix="/api")
app.include_router(codebase_router, prefix="/api")
app.include_router(patches_router, prefix="/api")
