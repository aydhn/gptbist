from pathlib import Path
from typing import Any

import dotenv


def get_default_env_file() -> Path:
    """Returns the default path to the .env file at the project root."""
    return Path(__file__).parent.parent.parent / ".env"

def load_env_file(path: Path | None = None, override: bool = False) -> bool:
    """
    Loads environment variables from the specified .env file.
    Returns True if the file exists and was loaded (or attempted), False otherwise.
    """
    env_path = path or get_default_env_file()

    if not env_path.exists():
        return False

    return dotenv.load_dotenv(dotenv_path=env_path, override=override)

def env_file_status(path: Path | None = None) -> dict[str, Any]:
    """
    Returns a safe dictionary summarizing the status of the .env file
    without exposing any secret values.
    """
    env_path = path or get_default_env_file()

    return {
        "exists": env_path.exists(),
        "path": str(env_path),
        "loaded_possible": env_path.exists() and env_path.is_file(),
    }
