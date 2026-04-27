from langchain_core.tools import tool

@tool("code_complexity_checker", return_direct=True)
def check_code_complexity(code_snippet: str) -> dict:

    """
    Analyzes the structural complexity of a code snippet. Returns line count, number of functions defined, and maximum nesting depth. Use this tool when you need to assess how complex or maintainable a piece of code is.
    """

    lines = [l for l in code_snippet.splitlines() if l.strip()]  # ignore blank lines
    line_count = len(lines)
    function_count = code_snippet.count("def ")
    max_nesting = max((len(line) - len(line.lstrip())) // 4 for line in lines) if lines else 0

    return {
        "line_count": line_count,
        "function_count": function_count,
        "max_nesting": max_nesting
    }