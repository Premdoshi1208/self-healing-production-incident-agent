from langchain_core.prompts import ChatPromptTemplate

from backend.services.llm_service import invoke_prompt


def generate_code_patch(
    incident,
    rca_analysis,
    fix_plan
):

    prompt = ChatPromptTemplate.from_template(
        """
You are an elite software reliability engineer.

A production incident occurred.

Your task:
1. Generate a safe production-ready code patch
2. Minimize deployment risk
3. Add proper cleanup and error handling
4. Follow production engineering best practices

Incident:
{incident}

RCA Analysis:
{rca_analysis}

Fix Plan:
{fix_plan}

Return your response in this format:

Code Patch:
```python
...
```

Patch Explanation:
...

Deployment Safety Notes:
...
"""
    )

    return invoke_prompt(prompt, {
        "incident": incident,
        "rca_analysis": rca_analysis,
        "fix_plan": fix_plan
    })
