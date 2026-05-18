"""Simple helper to drop & recreate the development SQLite DB.

Use this in development when you need the new `data_path` column.
For production use Alembic migrations instead.
"""
from src.api import database, models


def recreate_db():
    print("Dropping all tables...")
    models.Base.metadata.drop_all(bind=database.engine)
    print("Creating all tables...")
    models.Base.metadata.create_all(bind=database.engine)


if __name__ == "__main__":
    recreate_db()
