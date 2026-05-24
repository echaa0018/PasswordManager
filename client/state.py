from dataclasses import dataclass, field
from enum import Enum, auto
from client.vault import Vault


class AppState(Enum):
    LOCKED = auto()
    NORMAL = auto()
    BACKUP = auto()


@dataclass
class SessionState:
    state: AppState = AppState.LOCKED
    username: str | None = None
    master_key: bytes | None = None
    vault: Vault | None = None

    def clear(self) -> None:
        if self.master_key is not None:
            try:
                ba = bytearray(self.master_key)
                for i in range(len(ba)):
                    ba[i] = 0
            except Exception:
                pass
        self.master_key = None
        self.vault = None
        self.username = None
        self.state = AppState.LOCKED

    def is_read_only(self) -> bool:
        return self.state == AppState.BACKUP

    def is_authenticated(self) -> bool:
        return self.state in (AppState.NORMAL, AppState.BACKUP)
