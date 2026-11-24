"""Centralized repository paths and local environment loading."""

from dataclasses import dataclass
import os
from pathlib import Path


def repository_root() -> Path:
    """Find the checkout root for both editable and regular local installs."""
    configured = os.environ.get("PIPELINE_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()

    source_root = Path(__file__).resolve().parents[2]
    candidates = [source_root, Path.cwd().resolve(), *Path.cwd().resolve().parents]
    for candidate in dict.fromkeys(candidates):
        if (candidate / "daily" / "run-daily.sh").is_file() and (candidate / "pyproject.toml").is_file():
            return candidate
    return source_root


@dataclass(frozen=True)
class AppPaths:
    """Resolved paths used by the command line tools and dashboard."""

    root: Path
    projects: Path
    daily: Path
    dashboard: Path
    asset_library: Path
    skill: Path
    model_cache: Path
    mpt_storage: Path

    @classmethod
    def from_environment(cls) -> "AppPaths":
        root = repository_root()
        skill = Path(os.environ.get("SKILL_DIR", root / ".agents/skills/faceless-shorts")).expanduser().resolve()
        projects = Path(os.environ.get("PIPELINE_PROJECTS_DIR", root / "projects")).expanduser().resolve()
        return cls(
            root=root,
            projects=projects,
            daily=root / "daily",
            dashboard=root / "dashboard",
            asset_library=root / "asset-library",
            skill=skill,
            model_cache=root / "daily",
            mpt_storage=Path(os.environ.get("MPT_STORAGE", root / "mpt-storage")).expanduser().resolve(),
        )


PATHS = AppPaths.from_environment()


def load_repo_env(root: Path = PATHS.root) -> None:
    """Load optional .env values without overriding explicit process settings."""
    env_file = root / ".env"
    if not env_file.is_file():
        return
    for raw in env_file.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
