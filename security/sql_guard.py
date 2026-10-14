# security/sql_guard.py
# SQL injection prevention layer

import re

BLOCKED_KEYWORDS = [
    'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER',
    'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE', 'UNION',
    'SCRIPT', ';--', '/*', '*/', 'XP_', 'SYS.',
    'SLEEP', 'BENCHMARK', 'LOAD_FILE', 'INTO OUTFILE'
]

MAX_QUERY_LENGTH = 2000


class SQLGuard:
    def __init__(self):
        self.last_error = None

    def validate(self, sql: str) -> tuple:
        if not sql or not sql.strip():
            return False, "Empty query"

        if len(sql) > MAX_QUERY_LENGTH:
            return False, f"Query too long: {len(sql)}"

        sql_upper = sql.upper().strip()

        if not sql_upper.startswith('SELECT'):
            return False, "Only SELECT queries allowed"

        for keyword in BLOCKED_KEYWORDS:
            if keyword in sql_upper:
                return False, f"Blocked keyword: {keyword}"

        if ';' in sql:
            return False, "Semicolons not allowed"

        if '--' in sql or '/*' in sql:
            return False, "Comments not allowed"

        if 'LIMIT' not in sql_upper:
            sql = sql.rstrip() + " LIMIT 1000"

        return True, sql

    def sanitize_table_name(self, name: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_]', '', name)

    def sanitize_column_name(self, name: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_]', '', name)


def is_safe_sql(sql: str) -> tuple:
    guard = SQLGuard()
    return guard.validate(sql)