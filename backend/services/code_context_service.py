from pathlib import Path


def _read_excerpt(root_path, relative_path, max_chars):
    path = Path(root_path) / relative_path

    if not path.exists() or not path.is_file():
        return {
            "file_path": relative_path,
            "excerpt": "",
            "total_file_length": 0,
            "truncated": False,
            "error": f"File not found: {relative_path}",
        }

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as error:
        return {
            "file_path": relative_path,
            "excerpt": "",
            "total_file_length": 0,
            "truncated": False,
            "error": f"Unable to read file: {type(error).__name__}: {error}",
        }

    excerpt = text[:max_chars]

    return {
        "file_path": relative_path,
        "excerpt": excerpt,
        "total_file_length": len(text),
        "truncated": len(text) > len(excerpt),
    }


def build_code_context(codebase_search_result, max_files=4, max_chars_per_file=6000):
    if not codebase_search_result:
        return {
            "status": "skipped",
            "skipped_reason": "code context skipped: no codebase search result was provided",
            "files": [],
        }

    if codebase_search_result.get("status") != "completed":
        return {
            "status": "skipped",
            "skipped_reason": codebase_search_result.get(
                "skipped_reason",
                "code context skipped: codebase search did not complete",
            ),
            "files": [],
        }

    root_path = codebase_search_result.get("root_path")
    suspected_files = codebase_search_result.get("suspected_files") or []

    if not root_path:
        return {
            "status": "skipped",
            "skipped_reason": "code context skipped: missing codebase root path",
            "files": [],
        }

    context_files = []

    for file_result in suspected_files[:max_files]:
        relative_path = file_result.get("file_path")

        if not relative_path:
            continue

        entry = _read_excerpt(root_path, relative_path, max_chars_per_file)
        entry["relevance_score"] = file_result.get("relevance_score")
        entry["matched_terms"] = file_result.get("matched_terms", [])
        entry["short_reason"] = file_result.get("short_reason")
        context_files.append(entry)

    return {
        "status": "completed" if context_files else "skipped",
        "root_path": root_path,
        "files": context_files,
        "max_files": max_files,
        "max_chars_per_file": max_chars_per_file,
    }
