from pathlib import Path

FILES = [
    "core/views/__init__.py",
    "core/views/tenant.py",
    "tests/test_view_isolation.py",
]

for file in FILES:
    p = Path(file)

    # read text safely
    text = p.read_text(encoding="utf-8", errors="replace")

    # normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # remove BOM if exists
    text = text.replace("\ufeff", "")

    # replace NBSP with normal space
    text = text.replace("\u00A0", " ")

    # write clean UTF-8 LF
    p.write_text(text, encoding="utf-8", newline="\n")

    print("Normalized:", file)

print("DONE")
