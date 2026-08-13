from pathlib import Path

p = Path(__file__).resolve().parents[1] / "projects-panel.js"
t = p.read_text(encoding="utf-8")
for i, line in enumerate(t.splitlines(), 1):
    if any(c in line for c in "\u2014\u2013\u2018\u2019\u201c\u201d"):
        print(f"{i}: {line[:120]}")
t2 = (
    t.replace("\u2014", "-")
    .replace("\u2013", "-")
    .replace("\u2018", "'")
    .replace("\u2019", "'")
    .replace("\u201c", '"')
    .replace("\u201d", '"')
)
p.write_text(t2, encoding="utf-8", newline="\n")
t3 = p.read_text(encoding="utf-8")
print(
    "CLEAN"
    if not any(c in t3 for c in "\u2014\u2013\u2018\u2019\u201c\u201d")
    else "STILL_BAD"
)
