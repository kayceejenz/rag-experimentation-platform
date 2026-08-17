from typing import Protocol

from modules.auth.models.password_account_model import PasswordAccount


class AuthenticationRecorder(Protocol):
    def record_success(self, account: PasswordAccount) -> None: ...
    def record_failure(self, account: PasswordAccount) -> None: ...
