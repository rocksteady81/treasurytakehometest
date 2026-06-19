from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
PACKAGE_DIR = DIST / "ttb-label-compliance-prototype"
ZIP_PATH = DIST / "ttb-label-compliance-prototype.zip"

INCLUDE_PATHS = [
    ".gitignore",
    "README.md",
    "PROJECT_STATUS.md",
    "phase-1-requirements.md",
    "app.py",
    "ttb_rules.py",
    "run.command",
    "Procfile",
    "render.yaml",
    "requirements.txt",
    "package_submission.py",
    "docs",
    "samples",
    "tests",
]

EXCLUDE_NAMES = {"__pycache__", ".DS_Store"}
EXCLUDE_SUFFIXES = {".pyc"}


def should_exclude(path: Path) -> bool:
    return any(part in EXCLUDE_NAMES for part in path.parts) or path.suffix in EXCLUDE_SUFFIXES


def copy_path(source: Path, destination: Path) -> None:
    if should_exclude(source):
        return
    if source.is_dir():
        for child in source.rglob("*"):
            if should_exclude(child):
                continue
            relative = child.relative_to(source)
            target = destination / relative
            if child.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(child, target)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def build_package() -> Path:
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    DIST.mkdir(exist_ok=True)
    PACKAGE_DIR.mkdir(parents=True)

    for include_path in INCLUDE_PATHS:
        source = ROOT / include_path
        if not source.exists():
            continue
        copy_path(source, PACKAGE_DIR / include_path)

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    shutil.make_archive(str(ZIP_PATH.with_suffix("")), "zip", DIST, PACKAGE_DIR.name)
    return ZIP_PATH


if __name__ == "__main__":
    path = build_package()
    print(f"Built submission package: {path}")
