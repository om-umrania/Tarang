"""Keep PostgreSQL's integer flag binding covered without a running server."""

from unittest.mock import Mock

from tarang.store import PostgresConnection


def test_integer_flags_preserve_false_and_true_at_psycopg_boundary():
    connection = Mock()
    db = PostgresConnection(connection)
    db.execute("UPDATE evidence SET verifies=? WHERE id=?", (True, 7))
    db.execute("UPDATE commitments SET paused=? WHERE id=?", (False, 8))
    for call, expected in zip(connection.execute.call_args_list, [(1, 7), (0, 8)]):
        parameters = call.args[1]
        assert parameters == expected
        assert type(parameters[0]) is int
