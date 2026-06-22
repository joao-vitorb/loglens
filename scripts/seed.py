from pathlib import Path

from app import create_app
from app.extensions import db
from app.services.ingestion_service import build_ingestion_service

SAMPLE_FILE = Path(__file__).resolve().parent.parent / "seeds" / "sample.log"


def main() -> None:
    app = create_app()
    with app.app_context():
        db.create_all()
        content = SAMPLE_FILE.read_text(encoding="utf-8")
        result = build_ingestion_service().ingest_text(content)
        print(f"ingested={result.ingested} skipped={result.skipped}")


if __name__ == "__main__":
    main()
