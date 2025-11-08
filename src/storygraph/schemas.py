PLANNER_SCHEMA = {
    "template": str,
    "beats": list,  # [{id, purpose, target_words}]
    "motifs": list,
}
DRAFT_SCHEMA = {"scene_id": str, "text": str, "flags": list}
FACT_SCHEMA = {"links": list, "suggestions": list}
REVISION_SCHEMA = {"patches": list}
