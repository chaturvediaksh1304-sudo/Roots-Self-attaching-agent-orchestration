"""Per-project Roots settings and `roots init` scaffolding."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

CONFIG_REL = Path(".roots/config.yaml")


class ProjectConfig(BaseModel):
    language: str = "unknown"
    framework: str = "unknown"
    backend: str = Field(default="anthropic")  # adapters/base.py::load_adapter name
    model: str = "claude-sonnet-5"


# (detector filename, language, framework-hint) — first match wins per axis.
_LANGUAGE_MARKERS: list[tuple[str, str]] = [
    ("pyproject.toml", "python"),
    ("requirements.txt", "python"),
    ("setup.py", "python"),
    ("package.json", "node"),
    ("Cargo.toml", "rust"),
    ("go.mod", "go"),
    ("pom.xml", "java"),
    ("Gemfile", "ruby"),
]


def scan_project(root: Path) -> ProjectConfig:
    """Lightweight project-type detection. Reads only top-level marker files —
    no deep tree walk."""
    language = "unknown"
    for marker, lang in _LANGUAGE_MARKERS:
        if (root / marker).exists():
            language = lang
            break

    framework = _detect_framework(root, language)
    return ProjectConfig(language=language, framework=framework)


def _detect_framework(root: Path, language: str) -> str:
    if language == "node" and (root / "package.json").exists():
        try:
            import json

            pkg = json.loads((root / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            for name in ("next", "react", "vue", "svelte", "express"):
                if name in deps:
                    return name
        except (ValueError, OSError):
            return "unknown"
    if language == "python":
        for marker, fw in (("manage.py", "django"), ("mkdocs.yml", "mkdocs")):
            if (root / marker).exists():
                return fw
    return "unknown"


def load_config(root: Path) -> ProjectConfig:
    path = root / CONFIG_REL
    if not path.exists():
        raise FileNotFoundError(
            f"no {CONFIG_REL} found in {root}. Run `roots init` first."
        )
    data = yaml.safe_load(path.read_text()) or {}
    return ProjectConfig(**data)


def init_project(root: Path) -> ProjectConfig:
    """Scan the project, create the .roots/ tree, write config.yaml.
    Idempotent: re-running preserves an existing config's backend/model choice."""
    config = scan_project(root)

    existing = root / CONFIG_REL
    if existing.exists():
        prior = load_config(root)
        config.backend = prior.backend
        config.model = prior.model

    for sub in (".roots", ".roots/agents", ".roots/history"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    existing.write_text(yaml.safe_dump(config.model_dump(), sort_keys=True))
    return config
