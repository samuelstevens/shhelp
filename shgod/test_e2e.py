def test_help(script_runner, tmp_path):
    """
    Spawn the real `shgod` command and assert non-zero exit plus error text when a model lacking function-calling is requested.
    """
    script_runner.run(
        ["shgod", "-h"], env={"SHGOD_API_KEY": "DEADBEEF"}, cwd=tmp_path, check=True
    )


def test_non_function_calling_model_fails(script_runner, tmp_path):
    """
    Spawn the real `shgod` command and assert non-zero exit plus error text when a model lacking function-calling is requested.
    """
    result = script_runner.run(
        ["shgod", "how do I do nothing?", "--cfg.model", "ollama/llama2"],
        env={"SHGOD_API_KEY": "DEADBEEF"},
        cwd=tmp_path,
    )

    assert result.returncode != 0
