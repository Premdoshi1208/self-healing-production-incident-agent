from fastapi import APIRouter

from backend.memory.reflexion_memory import load_memories

router = APIRouter()


@router.get("/memory")
def get_reflexion_memories():
    memories = load_memories()

    return {
        "total_memories": len(memories),
        "memories": memories
    }


@router.get("/memory/recent")
def get_recent_memories():
    memories = load_memories()

    recent_memories = memories[-5:]

    return {
        "total_returned": len(recent_memories),
        "memories": recent_memories
    }