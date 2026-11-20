from pathlib import Path

import pytest

import action
from action import BadInputException, Output, get_input, resolve_artifact_path


def test_get_input_required_missing(monkeypatch):
    monkeypatch.delenv("ARTIFACT_PATH", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    with pytest.raises(BadInputException, match="artifact-path"):
        get_input("ARTIFACT_PATH", True)


def test_get_input_optional_missing(monkeypatch):
    monkeypatch.delenv("VERSION", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert get_input("VERSION", False) is None


def test_get_input_present(monkeypatch):
    monkeypatch.setenv("NAME", "widget")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert get_input("NAME", True) == "widget"


def test_output_write_github(tmp_path, monkeypatch):
    out_file = tmp_path / "github_output"
    out_file.write_text("")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_OUTPUT", str(out_file))

    output = Output()
    output.upload_id = "up-1"
    output.uploaded = True
    output.asset_id = "asset-1"
    output.write()

    content = out_file.read_text()
    assert "upload-id=up-1" in content
    assert "uploaded=true" in content
    assert "asset-id=asset-1" in content


def test_output_write_self_hosted(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.chdir(tmp_path)

    output = Output()
    output.upload_id = "up-2"
    output.uploaded = False
    output.asset_id = "asset-2"
    output.write()

    env_file = tmp_path / action.SELF_HOSTED_OUTPUT_FILE
    content = env_file.read_text()
    assert "UPLOAD_ID=up-2" in content
    assert "UPLOADED=false" in content
    assert "ASSET_ID=asset-2" in content


def test_resolve_artifact_path_relative(tmp_path, monkeypatch):
    artifact = tmp_path / "dist" / "pkg.whl"
    artifact.parent.mkdir()
    artifact.write_bytes(b"wheel")
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))

    resolved = resolve_artifact_path("dist/pkg.whl")
    assert Path(resolved) == artifact.resolve()


def test_resolve_artifact_path_absolute(tmp_path):
    artifact = tmp_path / "file.bin"
    artifact.write_bytes(b"data")

    resolved = resolve_artifact_path(str(artifact))
    assert Path(resolved) == artifact.resolve()


def test_resolve_artifact_path_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
    with pytest.raises(BadInputException, match="Artifact not found"):
        resolve_artifact_path("missing.bin")
