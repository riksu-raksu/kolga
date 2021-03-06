import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from shlex import quote
from typing import Any, Dict, List, Optional

import environs

from scripts.settings import settings
from scripts.utils.models import SubprocessResult

from .url import URL, make_url  # type: ignore

env = environs.Env()

MYSQL = "mysql"
POSTGRES = "postgresql"


def camel_case_split(camel_case_string: str) -> str:
    split_string_list = re.findall(
        r"[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))", camel_case_string
    )
    split_string = " ".join(split_string_list)
    return split_string.capitalize()


def loads_json(string: str) -> Dict[str, Any]:
    try:
        result = json.loads(string)
    except Exception:
        result = {}

    if not isinstance(result, dict):
        raise TypeError("Incorrect result")

    return result


def get_deploy_name(track: Optional[str] = None) -> str:
    track_postfix = f"-{track}" if track and track != settings.DEFAULT_TRACK else ""
    deploy_name = f"{settings.ENVIRONMENT_SLUG}{track_postfix}"
    return deploy_name


def get_secret_name(track: Optional[str] = None) -> str:
    deployment_name = get_deploy_name(track)
    secret_name = f"{deployment_name}-secret"

    return secret_name


def get_database_type() -> Optional[str]:
    if settings.MYSQL_ENABLED:
        return MYSQL
    elif settings.POSTGRES_ENABLED:
        return POSTGRES
    return None


def get_database_url(track: str) -> Optional[URL]:
    """
    Get the database URL based on the environment

    How the database URL is selected:
    1. If a predefined URL for the track is set, use that
    2. If no predefined URL is set, generate one based on the preferred database type
    """
    database_default_port_mapping = {MYSQL: 3306, POSTGRES: 5432}

    uppercase_track = track.upper()
    track_database_url = env.str(f"K8S_{uppercase_track}_DATABASE_URL", "")
    if track_database_url:
        return make_url(track_database_url)

    database_type = get_database_type()
    if not database_type:
        return None

    deploy_name = get_deploy_name(track)
    database_port = database_default_port_mapping[database_type]
    database_host = f"{deploy_name}-db-{database_type}"

    database_url = (
        f""
        f"{database_type}://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}"
        f"@{database_host}:{database_port}"
        f"/{settings.DATABASE_DB}"
    )

    return make_url(database_url)


def get_environment_vars_by_prefix(prefix: str) -> Dict[str, str]:
    """
    Extract all environment variables with a prefix

    Environment variables strting with the `prefix` attribute are
    extracted and put into a dict with the `prefix` removed.

    Args:
        prefix: Prefix to environment key that should be extracted

    Returns:
        A dict of keys stripped of the prefix and the value as given
        in the environment variable.
    """
    return {
        key[len(prefix) :]: value
        for key, value in os.environ.items()
        if key.startswith(prefix)
    }


def run_os_command(
    command_list: List[str], shell: bool = False, input: Optional[str] = None,
) -> SubprocessResult:
    command = command_list if not shell else " ".join(map(quote, command_list))

    result = subprocess.run(
        command, encoding="UTF-8", capture_output=True, input=input, shell=shell,
    )

    return SubprocessResult(
        out=result.stdout,
        err=result.stderr,
        return_code=result.returncode,
        child=result,
    )


def current_rfc3339_datetime() -> str:
    local_time = datetime.now(timezone.utc).astimezone()
    return local_time.isoformat()


def validate_file_secret_path(path: Path, valid_prefixes: List[str]) -> bool:
    absolute_path = str(path.absolute())
    return any(
        absolute_path.startswith(valid_prefix) for valid_prefix in valid_prefixes
    )
