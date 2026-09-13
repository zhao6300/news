from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_project_setup_files_exist():
    expected = [
        "README.md",
        "AGENTS.md",
        "PLAN.md",
        "Makefile",
        "src",
        "tests",
    ]
    for name in expected:
        assert (PROJECT_ROOT / name).exists()
