from pathlib import Path
from shutil import copy2, copytree, rmtree

from setuptools import setup


PROJECT_ROOT = Path(__file__).resolve().parent
BUILD_DIR = PROJECT_ROOT / "build"
LEGACY_PUBLISH_DIR = PROJECT_ROOT / "npm build"
STATIC_DIR = PROJECT_ROOT / "static"


def populate_publish_dirs() -> None:
    pages = [
        "index.html",
        "dashboard.html",
        "chat.html",
        "failures.html",
        "performance.html",
        "trends.html",
        "weekend.html",
        "login.html",
        "logout.html",
        "signin.html",
        "reset_password.html",
    ]

    aliases = [
        "dashboard",
        "chat",
        "failures",
        "performance",
        "trends",
        "weekend",
        "login",
        "logout",
        "signin",
        "reset_password",
    ]

    for folder in (BUILD_DIR, LEGACY_PUBLISH_DIR):
        if folder.exists():
            rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)

    for page in pages:
        source = PROJECT_ROOT / page
        if source.exists():
            copy2(source, BUILD_DIR / page)
            copy2(source, LEGACY_PUBLISH_DIR / page)

    for alias in aliases:
        source = PROJECT_ROOT / f"{alias}.html"
        if not source.exists():
            continue
        for folder in (BUILD_DIR, LEGACY_PUBLISH_DIR):
            target_dir = folder / alias
            target_dir.mkdir(parents=True, exist_ok=True)
            copy2(source, target_dir / "index.html")

    if STATIC_DIR.exists():
        copytree(STATIC_DIR, BUILD_DIR / "static", dirs_exist_ok=True)
        copytree(STATIC_DIR, LEGACY_PUBLISH_DIR / "static", dirs_exist_ok=True)


populate_publish_dirs()

setup(name="insight-leadership", version="0.0.0", py_modules=[])