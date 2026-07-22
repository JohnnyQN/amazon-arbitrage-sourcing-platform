from app.database.connection import DEFAULT_DB_PATH
from app.repositories.evaluation_repository import EvaluationRepository


def get_evaluation_repository() -> EvaluationRepository:
    """
    Provide the default SQLite evaluation repository.

    Tests override this dependency with a repository backed by a
    temporary database file.
    """
    return EvaluationRepository(db_path=DEFAULT_DB_PATH)