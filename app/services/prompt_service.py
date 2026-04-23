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

USER_PROMPT_TEMPLATE = """Here is the code snippet to analyze:
```{language}
{code_snippet}```
Strictness level: {strictness_level}
Strictness level is an integer from 1 to 10 that indicates how strict the analysis should be. A level of 1 means only critical issues should be reported, while a level of  10 means all issues, including minor ones, should be reported. Please analyze the code snippet based on the provided strictness level and return your analysis in the specified JSON format.""" 

def build_user_prompt(code_snippet: str, language: str, strictness_level: int) -> str:
    return USER_PROMPT_TEMPLATE.format(
        language=language,
        code_snippet=code_snippet,
        strictness_level=strictness_level
    )