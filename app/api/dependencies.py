from app.core.settings import get_settings
from app.repositories.evaluation_repository import EvaluationRepository


def get_evaluation_repository() -> EvaluationRepository:
    """
    FastAPI dependency that provides an EvaluationRepository.

    The database path is read from application settings so it can be
    configured via the ARBITRAGE_DATABASE_PATH environment variable.

    Called once per request. EvaluationRepository.__init__ calls
    initialize_database(), which is idempotent — safe to call repeatedly.

    Override this in tests via app.dependency_overrides to inject a
    tmp_path-backed repository without writing to the configured path.
    """
    return EvaluationRepository(db_path=get_settings().database_path)