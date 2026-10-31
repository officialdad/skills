import json
import os
import tempfile
from dataclasses import asdict, dataclass, field

MAX_TEAM_SIZE = 4
MAX_NAME_LENGTH = 40


@dataclass
class Team:
    name: str
    member_ids: list[int]
    channel_id: int = 0


@dataclass
class CreateResult:
    status: str
    team: Team | None = None
    user_id: int | None = None


@dataclass
class LeaveResult:
    team: Team
    disbanded: bool = False


def clean_name(name: str) -> str:
    return " ".join(name.split())


def name_key(name: str) -> str:
    return clean_name(name).casefold()


@dataclass
class TeamStore:
    path: str
    teams: dict[str, Team] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            with open(self.path, encoding="utf-8") as file:
                self.teams = {key: Team(**raw) for key, raw in json.load(file).items()}
        except FileNotFoundError:
            self.teams = {}

    def _save(self) -> None:
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)
        # Writing to a temp file first means a crash mid-write never leaves a half-written teams file.
        handle, temp_path = tempfile.mkstemp(dir=directory)
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            json.dump({key: asdict(team) for key, team in self.teams.items()}, file)
        os.replace(temp_path, self.path)

    def all(self) -> list[Team]:
        return list(self.teams.values())

    def get(self, name: str) -> Team | None:
        return self.teams.get(name_key(name))

    def team_of(self, user_id: int) -> Team | None:
        return next((team for team in self.teams.values() if user_id in team.member_ids), None)

    def create(self, name: str, member_ids: list[int]) -> CreateResult:
        # This runs without awaiting, so two simultaneous requests can't both claim a name or a member.
        name = clean_name(name)
        members = list(dict.fromkeys(member_ids))
        if not name or len(name) > MAX_NAME_LENGTH:
            return CreateResult("bad_name")
        if len(members) > MAX_TEAM_SIZE:
            return CreateResult("too_many")
        if name_key(name) in self.teams:
            return CreateResult("name_taken")
        for user_id in members:
            if self.team_of(user_id):
                return CreateResult("already_on_team", user_id=user_id)
        team = Team(name, members)
        self.teams[name_key(name)] = team
        self._save()
        return CreateResult("ok", team)

    def add_member(self, name: str, user_id: int) -> CreateResult:
        team = self.get(name)
        if team is None:
            return CreateResult("no_team")
        if user_id in team.member_ids:
            return CreateResult("already_member", team, user_id)
        if self.team_of(user_id):
            return CreateResult("already_on_team", team, user_id)
        if len(team.member_ids) >= MAX_TEAM_SIZE:
            return CreateResult("full", team)
        team.member_ids.append(user_id)
        self._save()
        return CreateResult("ok", team)

    def set_channel(self, name: str, channel_id: int) -> None:
        self.teams[name_key(name)].channel_id = channel_id
        self._save()

    def remove(self, name: str) -> Team | None:
        team = self.teams.pop(name_key(name), None)
        if team:
            self._save()
        return team

    def leave(self, user_id: int) -> LeaveResult | None:
        team = self.team_of(user_id)
        if team is None:
            return None
        team.member_ids.remove(user_id)
        if not team.member_ids:
            del self.teams[name_key(team.name)]
            self._save()
            return LeaveResult(team, disbanded=True)
        self._save()
        return LeaveResult(team)
