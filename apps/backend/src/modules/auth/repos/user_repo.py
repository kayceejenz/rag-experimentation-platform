from uuid import UUID

import psycopg
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.auth.models.error_model import AccountAlreadyExistsError
from modules.auth.models.password_account_model import PasswordAccount
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row


class UserRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    @staticmethod
    def account(row) -> PasswordAccount:
        user = AuthenticatedUser(
            row["id"], row["email"], row["display_name"], row["token_version"]
        )
        return PasswordAccount(
            user, row["password_hash"], row["is_active"], row["locked_until"]
        )

    def find_by_email(self, email: str) -> PasswordAccount | None:
        with self.connect() as db:
            row = db.execute(
                "select * from ragapp.users where email=%s and deleted_at is null",
                (email,),
            ).fetchone()
        return self.account(row) if row else None

    def find_by_id(self, user_id: UUID) -> PasswordAccount | None:
        with self.connect() as db:
            row = db.execute(
                "select * from ragapp.users where id=%s and deleted_at is null",
                (user_id,),
            ).fetchone()
        return self.account(row) if row else None

    def create(
        self, email: str, password_hash: str, display_name: str | None
    ) -> PasswordAccount:
        try:
            with self.connect() as db:
                row = db.execute(
                    "insert into ragapp.users(email,password_hash,display_name) "
                    "values(%s,%s,%s) returning *",
                    (email, password_hash, display_name),
                ).fetchone()
        except UniqueViolation:
            raise AccountAlreadyExistsError from None
        return self.account(row)

    def record_success(self, account: PasswordAccount) -> None:
        with self.connect() as db:
            db.execute(
                "update ragapp.users set failed_login_attempts=0, locked_until=null, "
                "last_login_at=now() where id=%s",
                (account.user.id,),
            )

    def record_failure(self, account: PasswordAccount) -> None:
        with self.connect() as db:
            db.execute(
                "update ragapp.users set failed_login_attempts=failed_login_attempts+1, "
                "locked_until=case when failed_login_attempts+1>=5 "
                "then now()+interval '15 minutes' else locked_until end where id=%s",
                (account.user.id,),
            )
