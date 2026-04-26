"""
Runtime checks. Import from core.apps so validators register.
"""
from django.core.checks import Warning, register
from django.db import connection
from django.db.utils import DatabaseError, OperationalError


@register
def check_mysql_utf8mb4_for_unicode(app_configs, **kwargs):
    """
    Warn if the MySQL session is not utf8mb4, which can mangle Devanagari (Nepali) and emoji.
    """
    if not connection.vendor == 'mysql':
        return []
    try:
        connection.ensure_connection()
    except (DatabaseError, OperationalError, OSError):
        return []
    try:
        with connection.cursor() as c:
            c.execute(
                'SELECT @@character_set_connection, @@collation_connection, '
                '@@character_set_database'
            )
            row = c.fetchone()
    except (DatabaseError, OperationalError):
        return []
    if not row:
        return []
    char, coll, dchar = row[0] or '', row[1] or '', row[2] or ''
    issues = []
    if char != 'utf8mb4':
        issues.append(
            Warning(
                'MySQL "character_set_connection" is not utf8mb4. Nepali (Devanagari) and '
                "full Unicode may be stored incorrectly. Set MYSQL_COLLATION in .env, use "
                "charset utf8mb4 in database OPTIONS, and create the database with "
                "CHARACTER SET utf8mb4 (see .env.example). "
                f'Current: character_set_connection={char!r}, collation={coll!r}.',
                id='core.W001',
            )
        )
    if dchar and dchar not in ('utf8mb4',) and dchar not in (None, ''):
        issues.append(
            Warning(
                "The default database is not using utf8mb4. New tables may inherit a "
                "suboptimal charset. Run: "
                f"ALTER DATABASE <name> CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; "
                f'(current schema default charset: {dchar!r})',
                id='core.W002',
            )
        )
    return issues
