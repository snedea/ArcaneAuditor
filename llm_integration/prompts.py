# llm_integration/prompts.py
def build_prompt(code_snippet, finding):
    # TODO: refine this prompt so that it will handle the entire list of findings, not just one.
    # TODO: add a section that will list the list of findings.
    # TODO: Refactor the Task section to simply provide a well formatted list of findings for the user to address.
    return f"""
    **Context:**
    I am reviewing a piece of Workday Extend DSL code. My static analysis tool has found the following issue.

    **Static Analysis Finding:**
    - **Rule ID:** {finding.rule.ID}
    - **Severity:** {finding.rule.SEVERITY}
    - **Description:** {finding.rule.DESCRIPTION}
    - **Violation Message:** {finding.message}

    **Code Snippet (with line numbers):**
    ```
    {code_snippet}
    ```

    **Your Task:**
    1.  Briefly explain in simple terms *why* this is a problem in a Workday context.
    2.  Provide a corrected code example that follows Workday Extend best practices.
    3.  If applicable, suggest a more robust alternative (e.g., using Workday Calculated Fields, System IDs, or other platform features instead of hardcoded values).
    4.  Format your response clearly using Markdown.
    """