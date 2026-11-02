"""Check the repository rules before committing (also runs automatically on GitHub for every push).

Usage:
    python tools/check_repo.py

Rules:
    - file names use only letters, digits, ".", "_", "-" and "/" (no spaces or special characters)
    - text files contain plain ASCII only
    - no model weights, datasets or large files in git (weights go to GitHub Releases)
    - no credentials (Kaggle tokens, GitHub tokens, private keys)
    - every Python file compiles

Only the Python standard library is used, so this runs anywhere.
"""
import py_compile
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {".md", ".py", ".ipynb", ".json", ".csv", ".txt", ".yaml", ".yml", ".cfg", ".toml"}
FORBIDDEN_SUFFIXES = {".pt", ".pth", ".onnx", ".pte", ".engine", ".zip", ".tar", ".gz"}
MAX_FILE_MB = 5
# Built from pieces so this file does not match its own patterns
SECRET_PATTERNS = [re.compile(p) for p in ("KG" + r"AT_[0-9a-f]{16,}", "gh" + r"p_[A-Za-z0-9]{20,}",
                                            "-----BEGIN " + r"[A-Z ]*PRIVATE KEY-----", r'"ke' + r'y"\s*:\s*"[0-9a-f]{32}"')]


def tracked_files():
    """Files git would commit (tracked plus new, minus ignored); falls back to all files outside .git."""
    try:
        out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=REPO,
                             capture_output=True, text=True, check=True).stdout
        return [REPO / line for line in out.splitlines() if line and (REPO / line).is_file()]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in REPO.rglob("*") if p.is_file() and ".git" not in p.parts]


def main():
    """Run every check and exit with status 1 if anything is wrong."""
    problems = []
    for path in tracked_files():
        rel = path.relative_to(REPO).as_posix()
        if not re.fullmatch(r"[A-Za-z0-9._/\-]+", rel):
            problems.append(f"{rel}: file name has spaces or special characters")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            problems.append(f"{rel}: model weights or archives belong in a GitHub Release, not in git")
        if path.stat().st_size > MAX_FILE_MB * 1e6:
            problems.append(f"{rel}: larger than {MAX_FILE_MB} MB")
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {".gitignore", "README", "LICENSE"}:
            text = path.read_bytes().decode("utf-8", errors="replace")
            for number, line in enumerate(text.splitlines(), 1):
                bad = sorted({c for c in line if ord(c) > 127})
                if bad:
                    problems.append(f"{rel}:{number}: non-ASCII characters {bad}")
            if path.name != "check_repo.py" and any(p.search(text) for p in SECRET_PATTERNS):
                problems.append(f"{rel}: looks like it contains a credential")
        if path.suffix == ".py":
            try:
                py_compile.compile(str(path), doraise=True, cfile=str(Path("/tmp") / "check_repo_compile.pyc"))
            except py_compile.PyCompileError as error:
                problems.append(f"{rel}: does not compile: {error.msg.strip().splitlines()[-1]}")

    if problems:
        print("Repository check FAILED:")
        print("\n".join("  " + p for p in problems))
        sys.exit(1)
    print("Repository check passed.")


if __name__ == "__main__":
    main()
