from __future__ import annotations

import argparse
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import psycopg
from core.settings import Settings

MIGRATION_PATTERN = re.compile(r"^(?P<version>\d{3})_(?P<name>[a-z0-9_]+)\.sql$")
TRANSACTION_PATTERN = re.compile(
    r"\A\s*begin;\s*(?P<body>.*?)\s*commit;\s*\Z", re.IGNORECASE | re.DOTALL
)
LOCK_NAME = "ragapp_schema_migrations"


@dataclass(frozen=True)
class Migration:
    version: int
    filename: str
    checksum: str
    sql: str


def migration_directory() -> Path:
    return Path(__file__).resolve().parent / "migrations"


def discover_migrations(directory: Path | None = None) -> list[Migration]:
    root = directory or migration_directory()
    migrations: list[Migration] = []
    versions: set[int] = set()
    for path in sorted(root.glob("*.sql")):
        match = MIGRATION_PATTERN.fullmatch(path.name)
        if not match:
            raise RuntimeError(f"Invalid migration filename: {path.name}")
        version = int(match.group("version"))
        if version in versions:
            raise RuntimeError(f"Duplicate migration version: {version:03d}")
        versions.add(version)
        raw = path.read_bytes()
        source = raw.decode("utf-8")
        transaction = TRANSACTION_PATTERN.fullmatch(source)
        if not transaction:
            raise RuntimeError(
                f"Migration {path.name} must contain one outer BEGIN/COMMIT transaction"
            )
        migrations.append(
            Migration(
                version=version,
                filename=path.name,
                checksum=hashlib.sha256(raw).hexdigest(),
                sql=transaction.group("body").strip(),
            )
        )
    if not migrations:
        raise RuntimeError(f"No migrations found in {root}")
    return migrations


def database_url() -> str:
    url = os.environ.get("MIGRATION_DATABASE_URL") or Settings().database_url
    if not url:
        raise RuntimeError("MIGRATION_DATABASE_URL or DATABASE_URL is required")
    hostname = urlparse(url).hostname or ""
    if "-pooler." in hostname:
        raise RuntimeError(
            "Migrations require Neon's direct connection URL, not the -pooler endpoint"
        )
    return url


def ensure_ledger(connection: psycopg.Connection) -> None:
    connection.execute("create schema if not exists ragapp")
    connection.execute(
        """
        create table if not exists ragapp.schema_migrations (
            version integer primary key,
            filename text not null unique,
            checksum char(64) not null,
            applied_at timestamptz not null default now()
        )
        """
    )


def applied_migrations(connection: psycopg.Connection) -> dict[int, tuple[str, str]]:
    rows = connection.execute(
        "select version, filename, checksum from ragapp.schema_migrations order by version"
    ).fetchall()
    return {
        int(version): (str(filename), str(checksum))
        for version, filename, checksum in rows
    }


def validate_history(
    migrations: list[Migration], applied: dict[int, tuple[str, str]]
) -> None:
    available = {migration.version: migration for migration in migrations}
    for version, (filename, checksum) in applied.items():
        migration = available.get(version)
        if migration is None:
            raise RuntimeError(
                f"Applied migration {version:03d} ({filename}) is missing"
            )
        if migration.filename != filename or migration.checksum != checksum:
            raise RuntimeError(
                f"Applied migration {version:03d} was modified; create a new migration instead"
            )


def migrate(*, status_only: bool = False) -> None:
    migrations = discover_migrations()
    with psycopg.connect(database_url(), autocommit=True) as connection:
        ensure_ledger(connection)
        connection.execute("select pg_advisory_lock(hashtext(%s))", (LOCK_NAME,))
        try:
            applied = applied_migrations(connection)
            validate_history(migrations, applied)
            pending = [
                migration
                for migration in migrations
                if migration.version not in applied
            ]
            if status_only:
                for migration in migrations:
                    state = "applied" if migration.version in applied else "pending"
                    print(f"{migration.filename}: {state}")
                return
            if not pending:
                print("Database schema is up to date")
                return
            for migration in pending:
                print(f"Applying {migration.filename}")
                with connection.transaction():
                    connection.execute(migration.sql)
                    connection.execute(
                        """
                        insert into ragapp.schema_migrations (version, filename, checksum)
                        values (%s, %s, %s)
                        """,
                        (migration.version, migration.filename, migration.checksum),
                    )
            print(f"Applied {len(pending)} migration(s)")
        finally:
            connection.execute("select pg_advisory_unlock(hashtext(%s))", (LOCK_NAME,))


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply migrations")
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show migration status without applying changes",
    )
    args = parser.parse_args()
    migrate(status_only=args.status)


if __name__ == "__main__":
    main()
