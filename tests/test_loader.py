from pathlib import Path

from app.ingestion.loader import load_text_file


def test_load_text_file():

    project_root = Path(__file__).resolve().parents[1]

    file_path = (
        project_root
        / "data"
        / "sample"
        / "hr_policy.txt"
    )

    text = load_text_file(str(file_path))

    print("\nDocument loaded successfully!")
    print("-" * 50)
    print(text)

    assert text