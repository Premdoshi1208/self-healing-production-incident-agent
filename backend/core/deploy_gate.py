def normalize_text(text):
    if not text:
        return ""

    return str(text).lower()


def evaluate_deploy_gate(
    incident,
    qa_validation,
    evaluation_result,
    test_result=None,
    patch_apply_result=None,
    real_patch=None
):
    """
    Deterministic deployment safety gate.

    Important:
    This is NOT an LLM decision.

    The LLM can recommend a deployment decision,
    but this gate makes the final safety decision using rules.
    """

    evaluation_result = evaluation_result or {}
    qa_text = normalize_text(qa_validation)

    verdict = evaluation_result.get("verdict", "UNKNOWN")
    overall_score = evaluation_result.get("overall_score", 0.0)

    qa_approved = (
        "approved" in qa_text
        and "rejected" not in qa_text
        and "not approved" not in qa_text
    )

    severity = normalize_text(incident.get("severity", "unknown"))

    blocking_reasons = []

    if not qa_approved:
        blocking_reasons.append(
            "QA validation did not approve the generated patch."
        )

    if verdict != "PASS":
        blocking_reasons.append(
            f"Evaluation verdict is {verdict}, not PASS."
        )

    if overall_score < 0.85:
        blocking_reasons.append(
            f"Evaluation score {overall_score} is below required threshold 0.85."
        )

    real_patch = real_patch or {}
    patch_apply_result = patch_apply_result or {}
    has_real_patch = bool(real_patch.get("unified_diff"))

    if has_real_patch and not patch_apply_result.get("applied"):
        blocking_reasons.append(
            "Real patch diff was generated but did not apply successfully in the isolated workspace."
        )

        if patch_apply_result.get("error"):
            blocking_reasons.append(
                f"Patch apply error: {patch_apply_result.get('error')}"
            )

    if test_result:
        tests_run = bool(test_result.get("tests_run")) or bool(test_result.get("command"))
        test_status = normalize_text(test_result.get("status"))
        test_passed = bool(test_result.get("passed")) or test_status == "passed"

        if tests_run and not test_passed:
            blocking_reasons.append(
                f"Deterministic test result is {test_result.get('status') or 'failed'}."
            )

    staging_allowed = len(blocking_reasons) == 0

    production_requires_human = True

    if severity in ["critical", "high"]:
        production_requires_human = True

    decision = {
        "staging_allowed": staging_allowed,
        "production_allowed": False,
        "production_requires_human": production_requires_human,
        "policy_engine": "deterministic_deploy_gate",
        "blocking_reasons": blocking_reasons,
        "test_result_considered": bool(test_result),
        "patch_apply_considered": bool(patch_apply_result),
        "real_patch_required_apply": has_real_patch,
        "decision_summary": ""
    }

    if staging_allowed:
        decision["decision_summary"] = (
            "Patch is approved for staging deployment. "
            "Production deployment still requires human approval."
        )
    else:
        decision["decision_summary"] = (
            "Patch is blocked from deployment because one or more safety checks failed."
        )

    return decision
