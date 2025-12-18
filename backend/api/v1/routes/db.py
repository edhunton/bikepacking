import os
from contextlib import contextmanager
from typing import Generator

import psycopg


def _dsn() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgres://postgres:postgres@localhost:55432/bikepacking",
    )


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    conn = psycopg.connect(_dsn())
    try:
        yield conn
    finally:
        conn.close()


