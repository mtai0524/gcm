import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_DIR = Path(__file__).resolve().parent.parent
GCM_PATH = REPO_DIR / "gcm"


@pytest.fixture
def core():
    """Load the extension-less `gcm` script as an importable module."""
    spec = importlib.util.spec_from_loader(
        "gcm", importlib.machinery.SourceFileLoader("gcm", str(GCM_PATH))
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["gcm"] = module
    spec.loader.exec_module(module)
    yield module
    sys.modules.pop("gcm", None)


@pytest.fixture
def git_repo(tmp_path, core, monkeypatch):
    """A fresh git repo as cwd, with core.REPO_ROOT pointed at it."""
    repo = tmp_path / "repo"
    repo.mkdir()
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    for args in (["init", "-q"], ["commit", "-q", "--allow-empty", "-m", "init"]):
        subprocess.run(["git", *args], cwd=repo, env=env, check=True)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(core, "REPO_ROOT", str(repo))
    return repo
