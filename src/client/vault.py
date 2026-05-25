import json
import uuid
from dataclasses import asdict, dataclass, field


@dataclass
class PasswordEntry:
    id: str
    service: str
    username: str
    password: str
    notes: str = ""

    @staticmethod
    def new(service: str, username: str, password: str, notes: str = "") -> "PasswordEntry":
        return PasswordEntry(
            id=str(uuid.uuid4()),
            service=service,
            username=username,
            password=password,
            notes=notes,
        )


@dataclass
class Vault:
    entries: list[PasswordEntry] = field(default_factory=list)

    def to_bytes(self) -> bytes:
        payload = {"entries": [asdict(e) for e in self.entries]}
        return json.dumps(payload).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "Vault":
        if not data:
            return cls()
        obj = json.loads(data.decode("utf-8"))
        entries = [PasswordEntry(**e) for e in obj.get("entries", [])]
        return cls(entries=entries)

    def add_entry(self, entry: PasswordEntry) -> None:
        if not entry.id:
            entry.id = str(uuid.uuid4())
        self.entries.append(entry)

    def update_entry(self, entry_id: str, **kwargs) -> bool:
        for entry in self.entries:
            if entry.id == entry_id:
                for key, value in kwargs.items():
                    if hasattr(entry, key) and key != "id":
                        setattr(entry, key, value)
                return True
        return False

    def delete_entry(self, entry_id: str) -> bool:
        for i, entry in enumerate(self.entries):
            if entry.id == entry_id:
                del self.entries[i]
                return True
        return False

    def get_entry(self, entry_id: str) -> PasswordEntry | None:
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None

    def list_entries(self) -> list[PasswordEntry]:
        return list(self.entries)
