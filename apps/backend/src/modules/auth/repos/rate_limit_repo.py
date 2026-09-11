from dataclasses import dataclass

from integrations.database import db_connection
from psycopg.rows import dict_row


@dataclass(frozen=True)
class RateLimitUsage:
    attempts: int
    retry_after_seconds: int


class AuthRateLimitRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def consume(
        self,
        action: str,
        client_key: str,
        window_seconds: int,
    ) -> RateLimitUsage:
        with db_connection(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "insert into ragapp.auth_rate_limits("
                "action,client_key,window_started_at,attempt_count) "
                "values(%s,%s,now(),1) "
                "on conflict(action,client_key) do update set "
                "attempt_count=case when ragapp.auth_rate_limits.window_started_at "
                "<=now()-make_interval(secs=>%s) then 1 "
                "else ragapp.auth_rate_limits.attempt_count+1 end,"
                "window_started_at=case when ragapp.auth_rate_limits.window_started_at "
                "<=now()-make_interval(secs=>%s) then now() "
                "else ragapp.auth_rate_limits.window_started_at end "
                "returning attempt_count, greatest(1,ceil(extract(epoch from ("
                "window_started_at+make_interval(secs=>%s)-now()))))::integer "
                "as retry_after_seconds",
                (action, client_key, window_seconds, window_seconds, window_seconds),
            ).fetchone()
        return RateLimitUsage(
            attempts=int(row["attempt_count"]),
            retry_after_seconds=int(row["retry_after_seconds"]),
        )
