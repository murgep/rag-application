import logging

from app.database.schema import create_schema


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Initializing database schema...")
    create_schema()
    logger.info("Database schema initialized successfully.")


if __name__ == "__main__":
    main()
