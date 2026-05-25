SYSTEM_PROMPT = """You are a senior code reviewer, you task is to analyze users code snippets utilizing secure coding, owasp top 10 vulnerabilities and clean code practices. Provide suggestions to user and violations based on these given practises and provide scoring on category, security, maintainabiliy, readability and overall. You should also provide a detailed explanation of the violations and suggestions to the user.

Return your response as JSON only, no extra text, in this exact format:
{
  "overall": float,
  "security": float,
  "maintainability": float,
  "readability": float,
  "violations": [list of strings],
  "suggestion": string
}
All scores must be between 0.0 and 10.0."""

BACKTICKS = "```"

USER_PROMPT_TEMPLATE = f"""Here is the code snippet to analyze:
{BACKTICKS}{{language}}
{{code_snippet}}{BACKTICKS}
Strictness level: {{strictness_level}}

{{context}}

Strictness level is an integer from 1 to 10..."""
def build_user_prompt(code_snippet: str, language: str, strictness_level: int, context: str = "") -> str:
    # Function logic: combine the user code and any retrieved evidence for review.
    context_section = f"Relevant context from knowledge base:\n{context}" if context else ""
    return USER_PROMPT_TEMPLATE.format(
        language=language,
        code_snippet=code_snippet,
        strictness_level=strictness_level,
        context=context_section
    )
