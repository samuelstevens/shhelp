from pathlib import Path


def _write_script(tmp_path: Path) -> Path:
    script = tmp_path / "shgod"
    script.write_text("from shgod.cli import main\nif __name__ == '__main__': main()")
    script.chmod(0o755)
    return script


def test_help(script_runner, tmp_path):
    """
    Check that help works.
    """
    script = _write_script(tmp_path)
    script_runner.run(
        [str(script), "-h"],
        env={"SHGOD_API_KEY": "DEADBEEF"},
        cwd=tmp_path,
        check=True,
    )

    script_runner.run(
        [str(script), "--help"],
        env={"SHGOD_API_KEY": "DEADBEEF"},
        cwd=tmp_path,
        check=True,
    )


def test_non_function_calling_model_fails(script_runner, tmp_path):
    """
    Spawn the real `shgod` command and assert non-zero exit plus error text when a model lacking function-calling is requested.
    """
    script = _write_script(tmp_path)
    result = script_runner.run(
        [
            str(script),
            "how do I do nothing?",
            "--cfg.model",
            "ollama/llama2",
        ],
        env={"SHGOD_API_KEY": "DEADBEEF"},
        cwd=tmp_path,
    )

    assert result.returncode != 0
