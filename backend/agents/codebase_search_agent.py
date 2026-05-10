import os
import re
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=False)

IGNORED_DIRS = {
    ".git",
    ".next",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "patch_workspaces",
}

SEARCHABLE_EXTENSIONS = {
    ".go",
    ".js",
    ".jsx",
    ".py",
    ".rb",
    ".ts",
    ".tsx",
    ".java",
    ".json",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
}

DOMAIN_TERMS = {
    "database": ["db", "database", "connection", "connections", "session", "pool", "query"],
    "auth": ["auth", "authenticate", "authentication", "login", "user", "password"],
    "latency": ["slow", "timeout", "latency", "p95", "delay"],
    "error": ["error", "exception", "failure", "failed"],
    "memory": ["memory", "leak", "cache", "global", "retained"],
}


def _project_relative_path(path):
    try:
        return path.resolve().relative_to(PROJECT_ROOT)
    except ValueError:
        return path.resolve()


def _configured_local_path():
    raw_path = os.getenv("CODEBASE_LOCAL_PATH")

    if not raw_path:
        default_target = PROJECT_ROOT / "target_repo"
        if default_target.exists():
            return default_target
        return None

    path = Path(raw_path).expanduser()

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path


def get_codebase_configuration():
    local_path = _configured_local_path()
    github_repo = os.getenv("GITHUB_REPO")
    github_token = os.getenv("GITHUB_TOKEN")
    github_default_branch = os.getenv("GITHUB_DEFAULT_BRANCH", "main")

    if local_path:
        return {
            "mode": "local",
            "local_path": str(local_path),
            "local_path_exists": local_path.exists(),
            "github_repo": github_repo,
            "github_default_branch": github_default_branch,
        }

    if github_repo:
        return {
            "mode": "github",
            "local_path": None,
            "local_path_exists": False,
            "github_repo": github_repo,
            "github_default_branch": github_default_branch,
            "github_token_configured": bool(github_token),
        }

    return {
        "mode": "disabled",
        "local_path": None,
        "local_path_exists": False,
        "github_repo": github_repo,
        "github_default_branch": github_default_branch,
    }


def _normalize_text(value):
    if value is None:
        return ""

    if isinstance(value, (list, tuple, set)):
        return " ".join(_normalize_text(item) for item in value)

    if isinstance(value, dict):
        return " ".join(f"{key} {_normalize_text(val)}" for key, val in value.items())

    return str(value)


def _tokenize(value):
    text = _normalize_text(value).lower()
    return re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", text)


def _extract_keywords(incident, rca_analysis):
    raw_terms = []
    raw_terms.extend(_tokenize(incident))
    raw_terms.extend(_tokenize(rca_analysis))

    terms = set(term.strip("_").lower() for term in raw_terms if len(term.strip("_")) >= 3)

    combined_text = " ".join(sorted(terms))
    for trigger, additions in DOMAIN_TERMS.items():
        if trigger in combined_text or any(addition in combined_text for addition in additions):
            terms.update(additions)

    stop_words = {
        "and",
        "are",
        "for",
        "from",
        "into",
        "not",
        "the",
        "this",
        "that",
        "with",
        "while",
        "after",
        "before",
        "service",
        "incident",
        "production",
    }

    return sorted(term for term in terms if term not in stop_words)[:80]


def _iter_searchable_files(root):
    for current_root, dirs, files in os.walk(str(root)):
        dirs[:] = [directory for directory in dirs if directory not in IGNORED_DIRS]

        for filename in files:
            path = Path(current_root) / filename
            if path.suffix.lower() in SEARCHABLE_EXTENSIONS:
                yield path


def _read_text_safely(path, max_chars=250000):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    return text[:max_chars]


def _preview_for_matches(text, matched_terms, max_chars=1400):
    if not text:
        return ""

    lowered = text.lower()
    first_index = None

    for term in matched_terms:
        index = lowered.find(term.lower())
        if index >= 0 and (first_index is None or index < first_index):
            first_index = index

    if first_index is None:
        return text[:max_chars]

    start = max(0, first_index - 350)
    end = min(len(text), start + max_chars)
    return text[start:end]


def _score_file(root, path, terms):
    relative_path = path.relative_to(root)
    relative_text = str(relative_path).replace(os.sep, "/").lower()
    content = _read_text_safely(path)
    lowered_content = content.lower()

    matched_terms = []
    score = 0.0

    for term in terms:
        term_lower = term.lower()
        path_hit = term_lower in relative_text
        content_hit = term_lower in lowered_content

        if path_hit or content_hit:
            matched_terms.append(term)

        if path_hit:
            score += 3.0

        if content_hit:
            occurrences = lowered_content.count(term_lower)
            score += min(occurrences, 5) * 1.0

    if path.suffix.lower() == ".py":
        score += 0.5

    if "test" in relative_text:
        score *= 0.35

    if not matched_terms:
        return None

    normalized_score = round(min(score / 20.0, 1.0), 2)

    reason_terms = ", ".join(matched_terms[:6])
    return {
        "file_path": str(relative_path).replace(os.sep, "/"),
        "relevance_score": normalized_score,
        "matched_terms": matched_terms[:20],
        "short_reason": f"Matched incident/RCA terms: {reason_terms}.",
        "code_preview": _preview_for_matches(content, matched_terms),
    }


def search_codebase_for_incident(incident, rca_analysis="", limit=8):
    config = get_codebase_configuration()

    if config["mode"] == "disabled":
        return {
            "status": "skipped",
            "mode": "disabled",
            "skipped_reason": "codebase analysis skipped: CODEBASE_LOCAL_PATH or GITHUB_REPO is not configured",
            "query_terms": [],
            "suspected_files": [],
        }

    if config["mode"] == "github":
        return {
            "status": "skipped",
            "mode": "github",
            "skipped_reason": (
                "codebase analysis skipped: GitHub mode is configured, but this demo "
                "search agent only inspects a local checkout. Set CODEBASE_LOCAL_PATH "
                "to analyze files locally."
            ),
            "github_repo": config.get("github_repo"),
            "query_terms": [],
            "suspected_files": [],
        }

    root = Path(config["local_path"])

    if not root.exists() or not root.is_dir():
        return {
            "status": "skipped",
            "mode": "local",
            "root_path": str(root),
            "root_path_display": str(_project_relative_path(root)),
            "skipped_reason": f"codebase analysis skipped: local path does not exist: {root}",
            "query_terms": [],
            "suspected_files": [],
        }

    terms = _extract_keywords(incident, rca_analysis)
    scored_files = []

    for path in _iter_searchable_files(root):
        result = _score_file(root, path, terms)
        if result:
            scored_files.append(result)

    scored_files.sort(key=lambda item: item["relevance_score"], reverse=True)

    return {
        "status": "completed",
        "mode": "local",
        "root_path": str(root),
        "root_path_display": str(_project_relative_path(root)),
        "query_terms": terms,
        "suspected_files": scored_files[:limit],
        "files_scanned": len(scored_files),
    }
