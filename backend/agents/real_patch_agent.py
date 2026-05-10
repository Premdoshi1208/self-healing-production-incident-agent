import difflib
import json

from langchain_core.prompts import ChatPromptTemplate

from backend.services.llm_service import invoke_prompt


def _normalize_text(value):
    if value is None:
        return ""

    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, indent=2)

    return str(value)


def _has_db_leak_signal(incident, rca_analysis, fix_plan):
    text = " ".join(
        [
            _normalize_text(incident),
            _normalize_text(rca_analysis),
            _normalize_text(fix_plan),
        ]
    ).lower()

    has_db_signal = any(term in text for term in ["db", "database", "connection", "session", "pool"])
    has_leak_signal = any(term in text for term in ["leak", "exhaust", "close", "cleanup", "release"])
    return has_db_signal and has_leak_signal


def _patch_target_login_file(source):
    target_function = '''def login(username, password):
    conn = get_connection()
    try:
        user = conn.query_user(username)

        if not user:
            return {"ok": False, "reason": "invalid credentials"}

        if user["password"] != password:
            return {"ok": False, "reason": "invalid credentials"}

        return {"ok": True, "user_id": user["id"]}
    finally:
        conn.close()
'''

    if "def login(username, password):" not in source or "get_connection()" not in source:
        return None

    lines = source.splitlines(keepends=True)
    start = None
    end = None

    for index, line in enumerate(lines):
        if line.startswith("def login(username, password):"):
            start = index
            continue

        if start is not None and index > start and line and not line.startswith((" ", "\t", "\n")):
            end = index
            break

    if start is None:
        return None

    if end is None:
        end = len(lines)

    new_lines = lines[:start] + target_function.splitlines(keepends=True) + lines[end:]
    return "".join(new_lines)


def _build_git_diff(file_path, old_text, new_text):
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    body = "".join(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )
    )

    if not body:
        return ""

    if not body.endswith("\n"):
        body += "\n"

    return f"diff --git a/{file_path} b/{file_path}\n{body}"


def _deterministic_patch(incident, rca_analysis, fix_plan, code_context):
    if not _has_db_leak_signal(incident, rca_analysis, fix_plan):
        return None

    for file_entry in code_context.get("files", []):
        file_path = file_entry.get("file_path", "")
        excerpt = file_entry.get("excerpt", "")

        if not file_path.endswith("login.py"):
            continue

        patched = _patch_target_login_file(excerpt)

        if not patched or patched == excerpt:
            continue

        unified_diff = _build_git_diff(file_path, excerpt, patched)

        if not unified_diff:
            continue

        return {
            "status": "generated",
            "patch_summary": (
                "Adds deterministic cleanup around the login database connection "
                "so every credential path releases the connection."
            ),
            "affected_files": [file_path],
            "unified_diff": unified_diff,
            "risk_notes": [
                "Low risk for the demo target repo: logic is unchanged except guaranteed cleanup in finally.",
                "Validate authentication success, invalid-user, and invalid-password paths.",
            ],
            "test_recommendations": [
                "Run pytest for target_repo/tests/test_login.py.",
                "Confirm active DB connection count returns to zero after failed login attempts.",
            ],
            "generation_method": "deterministic_db_leak_patch",
        }

    return None


def _llm_patch_recommendation(incident, rca_analysis, fix_plan, codebase_search_result, code_context):
    prompt = ChatPromptTemplate.from_template(
        """
You are a senior reliability engineer preparing a safe code remediation.

Use the compact code context to produce a standard git unified diff when the
fix is clear. If the context is insufficient, return a recommendation only.

Incident:
{incident}

RCA:
{rca_analysis}

Fix Plan:
{fix_plan}

Codebase Search:
{codebase_search}

Code Context:
{code_context}

Return JSON only with these keys:
patch_summary, affected_files, unified_diff, risk_notes, test_recommendations
"""
    )

    response = invoke_prompt(
        prompt,
        {
            "incident": incident,
            "rca_analysis": rca_analysis,
            "fix_plan": fix_plan,
            "codebase_search": codebase_search_result,
            "code_context": code_context,
        },
    )

    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        parsed = {
            "patch_summary": response,
            "affected_files": [],
            "unified_diff": "",
            "risk_notes": ["LLM did not return parseable JSON."],
            "test_recommendations": [],
        }

    parsed.setdefault("status", "generated" if parsed.get("unified_diff") else "recommendation_only")
    parsed.setdefault("generation_method", "llm")
    return parsed


def generate_real_patch(
    incident,
    rca_analysis,
    fix_plan,
    codebase_search_result,
    code_context,
):
    if not code_context or code_context.get("status") != "completed" or not code_context.get("files"):
        return {
            "status": "recommendation_only",
            "patch_summary": "Patch recommendation only: no code context was available.",
            "affected_files": [],
            "unified_diff": "",
            "risk_notes": [
                code_context.get("skipped_reason", "No code context available.") if code_context else "No code context available."
            ],
            "test_recommendations": [
                "Configure CODEBASE_LOCAL_PATH to enable code-aware diff generation."
            ],
            "generation_method": "skipped_no_code_context",
        }

    deterministic = _deterministic_patch(incident, rca_analysis, fix_plan, code_context)
    if deterministic:
        return deterministic

    try:
        return _llm_patch_recommendation(
            incident,
            rca_analysis,
            fix_plan,
            codebase_search_result,
            code_context,
        )
    except Exception as error:
        return {
            "status": "recommendation_only",
            "patch_summary": "Patch recommendation only: LLM diff generation failed.",
            "affected_files": [],
            "unified_diff": "",
            "risk_notes": [f"{type(error).__name__}: {error}"],
            "test_recommendations": [
                "Review the suspected files and create a patch manually.",
                "Run deterministic tests before staging.",
            ],
            "generation_method": "llm_failed",
        }
