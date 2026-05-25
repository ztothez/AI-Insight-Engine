from langchain_core.tools import tool

@tool("code_complexity_checker", return_direct=True)
def check_code_complexity(code_snippet: str) -> dict:

    """
    Analyzes the structural complexity of a code snippet. Returns line count, number of functions defined, and maximum nesting depth. Use this tool when you need to assess how complex or maintainable a piece of code is.
    """

    # Function logic: summarize size and nesting indicators used by the agent.
    lines = [l for l in code_snippet.splitlines() if l.strip()]  # ignore blank lines
    line_count = len(lines)
    function_count = code_snippet.count("def ")
    max_nesting = max((len(line) - len(line.lstrip())) // 4 for line in lines) if lines else 0

    return {
        "line_count": line_count,
        "function_count": function_count,
        "max_nesting": max_nesting
    }

@tool("search_best_practices", return_direct=True)
def search_best_practices(topic: str) -> str:
        """
        Searches for best practices related to a given programming topic. Use this tool when you want to find guidelines or recommendations for writing better code in a specific area.
        """
        # Function logic: provide the agent with a small built-in guidance lookup.
        best_practices = {
            "python": "Use list comprehensions for concise code, follow PEP 8 style guide, and prefer using 'with' statements for file handling.",
            "javascript": "Use 'const' and 'let' instead of 'var', follow Airbnb JavaScript style guide, and use promises or async/await for asynchronous code."
        }
        return best_practices.get(topic.lower(), "No best practices found for this topic.")
    
@tool("calculate_risk_score", return_direct=True)
def calculate_risk_score(security: float, maintainability: float, readability: float) -> dict:
    """
    Calculates overall risk score from individual quality scores.
    Security carries 50% weight, maintainability 30%, readability 20%.
    Use this when you need to assess overall code risk from individual quality scores.
    Returns risk_score (0-10) and risk_level (Low/Medium/High).
    """
    # Function logic: weight weaker quality scores into a business-facing risk level.
    risk_score = (10 - security) * 0.5 + (10 - maintainability) * 0.3 + (10 - readability) * 0.2
    risk_level = "Low" if risk_score < 3 else "Medium" if risk_score < 7 else "High"
    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level
    }
