import re


def normalize_text(text):
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def contains_any(text, keywords):
    text = normalize_text(text)

    for keyword in keywords:
        if keyword in text:
            return True

    return False


def keyword_overlap_score(expected_text, actual_text):
    expected_text = normalize_text(expected_text)
    actual_text = normalize_text(actual_text)

    if not expected_text or not actual_text:
        return 0.0

    expected_words = set(expected_text.split())
    actual_words = set(actual_text.split())

    if not expected_words:
        return 0.0

    overlap = expected_words.intersection(actual_words)

    return round(len(overlap) / len(expected_words), 2)


def semantic_root_cause_score(expected_root_cause, actual_rca):
    """
    Domain-aware root cause scoring.

    This avoids being too strict with exact wording.
    Example:
    'db.close missing' and 'unclosed database sessions'
    should be treated as semantically similar.
    """

    expected = normalize_text(expected_root_cause)
    actual = normalize_text(actual_rca)

    score = keyword_overlap_score(expected, actual)

    bonus = 0.0

    # Database / connection leak concept
    if contains_any(expected, ["database", "db", "session", "connection"]):
        if contains_any(actual, ["database", "db", "session", "connection"]):
            bonus += 0.20

    if contains_any(expected, ["close", "cleanup", "release"]):
        if contains_any(actual, ["close", "cleanup", "release", "unclosed", "not released"]):
            bonus += 0.20

    if contains_any(expected, ["leak", "leaking"]):
        if contains_any(actual, ["leak", "leaking", "exhausted", "pool exhausted"]):
            bonus += 0.20

    # Frontend null crash concept
    if contains_any(expected, ["frontend", "component", "null", "undefined"]):
        if contains_any(actual, ["frontend", "component", "null", "undefined", "render"]):
            bonus += 0.25

    # Memory leak concept
    if contains_any(expected, ["memory", "object", "global", "retained"]):
        if contains_any(actual, ["memory", "object", "global", "retained", "leak", "cache"]):
            bonus += 0.25

    return round(min(score + bonus, 1.0), 2)


def semantic_fix_score(expected_fix, actual_fix_plan):
    expected = normalize_text(expected_fix)
    actual = normalize_text(actual_fix_plan)

    score = keyword_overlap_score(expected, actual)

    bonus = 0.0

    if contains_any(expected, ["close", "cleanup", "session", "connection"]):
        if contains_any(actual, ["close", "cleanup", "finally", "context manager", "release"]):
            bonus += 0.30

    if contains_any(expected, ["null", "check"]):
        if contains_any(actual, ["null check", "guard", "fallback", "undefined"]):
            bonus += 0.30

    if contains_any(expected, ["release", "clear", "cache", "objects"]):
        if contains_any(actual, ["release", "clear", "cache", "memory", "garbage"]):
            bonus += 0.30

    return round(min(score + bonus, 1.0), 2)


def heuristic_evaluation(rca_analysis, fix_plan, qa_validation):
    """
    Production alerts do not come with hidden labels.
    For those runs we use a transparent heuristic evaluation so deploy gates
    can still reason about RCA/fix/QA quality without pretending ground truth exists.
    """
    rca_text = normalize_text(rca_analysis)
    fix_text = normalize_text(fix_plan)
    qa_text = normalize_text(qa_validation)

    root_cause_score = 0.0
    if contains_any(rca_text, ["root cause", "database", "connection", "memory", "frontend", "latency", "error"]):
        root_cause_score += 0.55
    if contains_any(rca_text, ["because", "indicates", "signals", "trace", "logs", "metrics"]):
        root_cause_score += 0.25
    if contains_any(rca_text, ["confidence", "important signals"]):
        root_cause_score += 0.20

    fix_score = 0.0
    if contains_any(fix_text, ["fix plan", "engineering changes", "cleanup", "close", "release", "guard", "rollback"]):
        fix_score += 0.45
    if contains_any(fix_text, ["required tests", "test", "staging", "rollback", "deployment risks"]):
        fix_score += 0.35
    if contains_any(fix_text, ["finally", "context manager", "connection", "null", "cache", "memory"]):
        fix_score += 0.20

    root_cause_score = round(min(root_cause_score, 1.0), 2)
    fix_score = round(min(fix_score, 1.0), 2)
    qa_approved = "approved" in qa_text and "rejected" not in qa_text and "not approved" not in qa_text

    overall_score = round(
        (root_cause_score * 0.45)
        + (fix_score * 0.35)
        + ((1.0 if qa_approved else 0.0) * 0.20),
        2
    )

    if overall_score >= 0.75:
        verdict = "PASS"
    elif overall_score >= 0.50:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    return {
        "evaluated": False,
        "evaluation_mode": "heuristic_no_hidden_labels",
        "root_cause_score": root_cause_score,
        "fix_score": fix_score,
        "qa_approved": qa_approved,
        "overall_score": overall_score,
        "verdict": verdict,
        "note": "No hidden labels were available because this came from a production-style alert. Used transparent heuristic evaluation instead."
    }


def evaluate_incident_response(
    original_incident,
    rca_analysis,
    fix_plan,
    qa_validation
):
    """
    Evaluates the AI workflow using hidden ground-truth labels.

    Important:
    These expected fields are NEVER shown to the AI agents.
    They are only used here after the agents finish.
    """

    expected_root_cause = original_incident.get("expected_root_cause")
    expected_fix = original_incident.get("expected_fix")

    if not expected_root_cause or not expected_fix:
        return heuristic_evaluation(rca_analysis, fix_plan, qa_validation)

    root_cause_score = semantic_root_cause_score(
        expected_root_cause,
        rca_analysis
    )

    fix_score = semantic_fix_score(
        expected_fix,
        fix_plan
    )

    qa_approved = "approved" in normalize_text(qa_validation)

    overall_score = round(
        (root_cause_score * 0.45)
        + (fix_score * 0.35)
        + ((1.0 if qa_approved else 0.0) * 0.20),
        2
    )

    if overall_score >= 0.75:
        verdict = "PASS"
    elif overall_score >= 0.50:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    return {
        "evaluated": True,
        "root_cause_score": root_cause_score,
        "fix_score": fix_score,
        "qa_approved": qa_approved,
        "overall_score": overall_score,
        "verdict": verdict,
        "note": "Evaluation used hidden labels after agent execution. The AI agents did not see the answers."
    }