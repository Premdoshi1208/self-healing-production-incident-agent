from backend.memory.reflexion_memory import load_memories


def retrieve_similar_memories(incident, max_results=3):
    memories = load_memories()

    similar_memories = []
    seen_keys = set()

    incident_title = incident["title"].lower()
    incident_service = incident["service"].lower()

    for memory in memories:
        memory_title = str(memory.get("incident_title", "")).lower()
        memory_service = str(memory.get("service", "")).lower()
        learning_summary = memory.get("learning_summary", "")

        title_match = incident_title in memory_title or memory_title in incident_title
        service_match = incident_service == memory_service

        if title_match or service_match:
            memory_key = (
                memory_title,
                memory_service,
                learning_summary
            )

            if memory_key in seen_keys:
                continue

            seen_keys.add(memory_key)

            similar_memories.append({
                "incident_title": memory.get("incident_title", "Unknown incident"),
                "service": memory.get("service", "unknown-service"),
                "learning_summary": learning_summary
            })

        if len(similar_memories) >= max_results:
            break

    return similar_memories
