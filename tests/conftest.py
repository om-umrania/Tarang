"""Optional isolated PostgreSQL parity checks; normal runs use SQLite."""

import os
import uuid
from urllib.parse import urlencode

import pytest


@pytest.fixture
def demo_database(tmp_path):
    base = os.getenv("TARANG_TEST_POSTGRES", "")
    if not base:
        yield str(tmp_path / "demo.sqlite3")
        return
    import psycopg
    from psycopg import sql

    schema = "tarang_test_" + uuid.uuid4().hex
    with psycopg.connect(base, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    separator = "&" if "?" in base else "?"
    try:
        yield base + separator + urlencode({"options": "-csearch_path=" + schema})
    finally:
        with psycopg.connect(base, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema))
            )
