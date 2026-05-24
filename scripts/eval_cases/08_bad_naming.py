"""Unreadable single-letter variable names — clean code violation."""

ID = "clean_bad_naming_01"
CATEGORY = "clean_code_violation"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''def calc(d, t, r):
    x = d * r
    y = x * t
    z = y + (y * 0.05)
    if z > 1000:
        a = z * 0.9
    else:
        a = z
    return a

def do_it(lst):
    r = []
    for i in lst:
        v = calc(i["d"], i["t"], i["r"])
        r.append({"id": i["id"], "v": v})
    return r
'''
EXPECTED = {
    "readability_score_max": 7.5,
    "should_contain_violations": [["naming", "variable name", "descriptive", "readability"]],
    "should_have_citations": True,
}
