"""
Builds eval_dataset.json from individual test case files in scripts/eval_cases/.

Each test case is a .py file that defines:
- ID: str
- CATEGORY: str
- LANGUAGE: str  (e.g. "python")
- STRICTNESS: int  (1-5)
- CODE: str  (the actual code snippet to test — multi-line is fine!)
- EXPECTED: dict  (what we expect the system to return)

This script reads all of them, builds a JSON list, and writes eval_dataset.json.
Handles all the escaping for you — write Python normally, no \\n tricks.
"""
import json
import importlib.util
from pathlib import Path


def load_case(path: Path) -> dict:
    """Load a single test case .py file as a Python module and extract its variables."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {
        "id": module.ID,
        "category": module.CATEGORY,
        "input": {
            "code_snippet": module.CODE,
            "language": module.LANGUAGE,
            "strictness_level": module.STRICTNESS,
        },
        "expected": module.EXPECTED,
    }


def main():
    cases_dir = Path(__file__).parent / "eval_cases"
    case_files = sorted(cases_dir.glob("*.py"))

    dataset = [load_case(p) for p in case_files]

    output_path = Path(__file__).parent / "eval_dataset.json"
    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"✓ Built {output_path} with {len(dataset)} test cases:")
    for case in dataset:
        print(f"  - {case['id']} ({case['category']})")


if __name__ == "__main__":
    main()