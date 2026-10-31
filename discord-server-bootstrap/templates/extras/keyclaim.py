import json
import os
import re
import time
from dataclasses import dataclass


def normalize_email(raw: str) -> str:
    return raw.strip().lower()


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{local[:1]}***@{domain}"


def load_keys(path: str) -> dict[str, str]:
    # The list format is unknown, so each line is split on any separator and matched by shape.
    keys: dict[str, str] = {}
    with open(path, encoding="utf-8-sig") as file:
        for line in file:
            tokens = [token.strip("\"' ") for token in re.split(r"[,;\t ]+", line.strip())]
            email = next((token for token in tokens if "@" in token), None)
            key = next((token for token in tokens if token.startswith("sk-")), None)
            if email and key:
                keys[normalize_email(email)] = key
    return keys


class ClaimStore:
    def __init__(self, path: str) -> None:
        self.path = path

    def _read(self) -> dict[str, int]:
        try:
            with open(self.path, encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def _write(self, claims: dict[str, int]) -> None:
        temp_path = f"{self.path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(claims, file)
        os.replace(temp_path, self.path)

    def owner_of(self, email: str) -> int | None:
        return self._read().get(email)

    def email_claimed_by(self, discord_id: int) -> str | None:
        return next((email for email, owner in self._read().items() if owner == discord_id), None)

    def set(self, email: str, discord_id: int) -> None:
        claims = self._read()
        claims[email] = discord_id
        self._write(claims)

    def clear(self, email: str) -> bool:
        claims = self._read()
        if email not in claims:
            return False
        del claims[email]
        self._write(claims)
        return True


class FailureLimiter:
    def __init__(self, max_failures: int = 5, window_seconds: int = 3600) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: dict[int, list[float]] = {}

    def _recent(self, user_id: int, now: float) -> list[float]:
        recent = [t for t in self._failures.get(user_id, []) if now - t < self.window_seconds]
        self._failures[user_id] = recent
        return recent

    def blocked(self, user_id: int, now: float | None = None) -> bool:
        return len(self._recent(user_id, now or time.time())) >= self.max_failures

    def record(self, user_id: int, now: float | None = None) -> None:
        now = now or time.time()
        self._recent(user_id, now).append(now)


@dataclass
class ClaimResult:
    status: str  # claimed, repeat, not_found, taken, other_email
    key: str | None = None


def claim_key(keys: dict[str, str], store: ClaimStore, email: str, discord_id: int) -> ClaimResult:
    email = normalize_email(email)
    key = keys.get(email)
    if key is None:
        return ClaimResult("not_found")

    owner = store.owner_of(email)
    if owner is None:
        # A member who already holds one key can't collect more by guessing emails.
        if store.email_claimed_by(discord_id) is not None:
            return ClaimResult("other_email")
        store.set(email, discord_id)
        return ClaimResult("claimed", key)
    if owner == discord_id:
        return ClaimResult("repeat", key)
    return ClaimResult("taken")
