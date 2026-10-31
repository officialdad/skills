#!/usr/bin/env python3
"""Publishes guide.md into a read-only #guide channel as one embed per section.

The first embed is a contents list with a jump link per section. The help bot links
to these messages instead of repeating long answers. Writes guide-index.md (titles,
links, short excerpts) for build-bot-config.sh.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://discord.com/api/v10"
EMBED_LIMIT = 3800
EXCERPT_LENGTH = 180
STATE_PATH = os.path.join(ROOT, "data", "guide-messages.json")
INDEX_PATH = os.path.join(ROOT, "guide-index.md")
PLACEHOLDER_ID = "0" * 19
# Optional. A JSON file maps plain-text phrases in the source to Discord timestamp markup, such as
# {"Sun 1 Nov, 1:00 PM": "<t:1793509200:f> (<t:1793509200:R>)"}. Discord shows it in each reader's own time zone.
SUBSTITUTIONS_PATH = os.path.join(ROOT, "substitutions.json")

EMBED_COLORS = {"contents": 0xFF6B5E, "overview": 0x5AA9FF, "step": 0x57C78A, "troubleshooting": 0xFF9F43, "appendix": 0xA78BFA}


@dataclass
class Section:
    heading: str
    level: int
    parent: str
    body: str

    @property
    def title(self) -> str:
        return f"{self.parent}: {self.heading}" if self.parent else self.heading

    @property
    def color(self) -> int:
        top = (self.parent or self.heading).lower()
        for prefix, key in (("step", "step"), ("troubleshooting", "troubleshooting"), ("appendix", "appendix")):
            if top.startswith(prefix):
                return EMBED_COLORS[key]
        return EMBED_COLORS["overview"]


def load_substitutions() -> dict[str, str]:
    try:
        with open(SUBSTITUTIONS_PATH, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def read_env(path: str) -> dict[str, str]:
    env = {}
    with open(path, encoding="utf-8") as file:
        for line in file:
            name, separator, value = line.strip().partition("=")
            if separator and not name.startswith("#"):
                env[name] = value.strip("\"'")
    return env


ENV = read_env(os.path.join(ROOT, ".env"))
GUILD = ENV["DISCORD_GUILD_ID"]


def call(method: str, path: str, body: dict | None = None):
    request = urllib.request.Request(
        API + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bot {ENV['DISCORD_BOT_TOKEN']}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (community-guide-sync, 1.0)",
        },
    )
    while True:
        try:
            with urllib.request.urlopen(request) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            if error.code == 429:
                time.sleep(float(json.loads(error.read()).get("retry_after", 1)) + 0.2)
                continue
            sys.exit(f"Discord error {error.code} on {method} {path}: {error.read().decode()[:300]}")


def slug(heading: str) -> str:
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", heading.lower()).strip())


def discord_markdown(text: str, anchors: dict[str, str]) -> str:
    # Discord renders no tables, checkboxes, rules or in-page anchors, so each becomes the closest thing it does render.
    lines = text.splitlines()
    out, index, in_fence = [], 0, False
    while index < len(lines):
        line = lines[index]
        if line.strip().startswith("```"):
            in_fence = not in_fence
        if in_fence or not line.strip().startswith("|"):
            if in_fence or line.strip() != "---":
                out.append(line if in_fence else re.sub(r"^(\s*)- \[ \] ", r"\1- ", line))
            index += 1
            continue

        table = []
        while index < len(lines) and lines[index].strip().startswith("|"):
            table.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
            index += 1
        header, rows = table[0], [row for row in table[2:]]
        out.extend(render_table(header, rows))

    result = "\n".join(out).strip()
    for plain, markup in load_substitutions().items():
        result = result.replace(plain, markup)
    return re.sub(
        r"\[([^\]]+)\]\(#([^)]+)\)",
        lambda match: f"[{match.group(1)}]({anchors[match.group(2)]})" if match.group(2) in anchors else match.group(1),
        result,
    )


def render_table(header: list[str], rows: list[list[str]]) -> list[str]:
    long_details = any(len(row[1]) > 150 for row in rows if len(row) > 1)
    out = []
    for row in rows:
        if len(header) > 2:
            details = " · ".join(f"{name}: {value}" for name, value in zip(header[1:], row[1:]))
            out += [f"**{row[0]}**", details, ""]
        elif long_details:
            out += [f"**{row[0]}**", row[1], ""]
        else:
            out.append(f"- **{row[0]}:** {row[1]}")
    return out


def split_sections(markdown: str) -> tuple[str, str, list[Section]]:
    intro_title, intro, sections = "", [], []
    current, parent, in_fence = None, "", False
    for line in markdown.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        match = None if in_fence else re.match(r"^(#{1,3}) (.+)$", line)
        if match:
            level, heading = len(match.group(1)), match.group(2)
            if level == 1:
                intro_title = heading
                continue
            if level == 2:
                parent = heading
            current = Section(heading, level, parent if level == 3 else "", "")
            sections.append(current)
            continue
        if current is None:
            intro.append(line)
        else:
            current.body += line + "\n"
    return intro_title, "\n".join(intro), sections


def chunk(text: str) -> list[str]:
    chunks, current = [], ""
    for block in re.split(r"\n{2,}", text):
        while len(block) > EMBED_LIMIT:
            cut = block.rfind("\n", 0, EMBED_LIMIT)
            cut = cut if cut > 0 else EMBED_LIMIT
            if current:
                chunks.append(current)
                current = ""
            chunks.append(block[:cut])
            block = block[cut:].lstrip("\n")
        if len(current) + len(block) + 2 > EMBED_LIMIT and current:
            chunks.append(current)
            current = block
        else:
            current = f"{current}\n\n{block}" if current else block
    if current:
        chunks.append(current)
    return chunks or [""]


def layout(intro_title: str, intro: str, sections: list[Section], message_ids: list[str] | None, channel: str):
    """Returns (embeds, section_start_offsets). Placeholder ids keep the message count stable before the real ids exist."""
    def url(offset: int) -> str:
        message_id = message_ids[offset] if message_ids and offset < len(message_ids) else PLACEHOLDER_ID
        return f"https://discord.com/channels/{GUILD}/{channel}/{message_id}"

    # Message counts must be known before links can be written, and link text never changes a chunk count.
    counts = [len(chunk(discord_markdown(section.body, {}))) for section in sections]

    def offsets_for(contents_count: int) -> list[int]:
        offsets, cursor = [], contents_count
        for count in counts:
            offsets.append(cursor)
            cursor += count
        return offsets

    contents_count = 1
    while True:
        offsets = offsets_for(contents_count)
        anchors = {}
        for section, offset in zip(sections, offsets):
            anchors.setdefault(slug(section.heading), url(offset))
        lines = [discord_markdown(intro, anchors), "", "**Jump to a section**"]
        for section, offset in zip(sections, offsets):
            lines.append(f"{'  ' if section.level == 3 else ''}- [{section.heading}]({url(offset)})")
        contents_chunks = chunk("\n".join(lines))
        if len(contents_chunks) == contents_count:
            break
        contents_count = len(contents_chunks)

    embeds = []
    for number, text in enumerate(contents_chunks, 1):
        title = intro_title if number == 1 else f"{intro_title} (contents, part {number})"
        embeds.append({"title": title, "description": text, "color": EMBED_COLORS["contents"]})
    for section in sections:
        parts = chunk(discord_markdown(section.body, anchors))
        for number, text in enumerate(parts, 1):
            title = section.title if len(parts) == 1 else f"{section.title} ({number}/{len(parts)})"
            embeds.append({"title": title[:256], "description": text, "color": section.color})
    return embeds, offsets


def ensure_channel() -> str:
    # discord-setup.sh owns the channel name, category and permissions, so this only needs its id.
    channel = ENV.get("DISCORD_GUIDE_CHANNEL_ID")
    if not channel:
        sys.exit("DISCORD_GUIDE_CHANNEL_ID is missing in .env. Run bootstrap.sh first.")
    return channel


def load_state() -> dict:
    try:
        with open(STATE_PATH, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def payload(embed: dict) -> dict:
    return {"content": "", "embeds": [embed], "allowed_mentions": {"parse": []}}


def main() -> None:
    with open(os.path.join(ROOT, "guide.md"), encoding="utf-8") as file:
        intro_title, intro, sections = split_sections(file.read())

    channel = ensure_channel()
    state = load_state()
    saved_ids = state["ids"] if state.get("channel") == channel else None

    embeds, offsets = layout(intro_title, intro, sections, saved_ids, channel)
    reuse = saved_ids is not None and len(saved_ids) == len(embeds)

    if reuse:
        message_ids = saved_ids
        for message_id, embed in zip(message_ids, embeds):
            call("PATCH", f"/channels/{channel}/messages/{message_id}", payload(embed))
    else:
        # A different section layout can't be edited in place, so repost everything in order.
        embeds, offsets = layout(intro_title, intro, sections, None, channel)
        while True:
            old = call("GET", f"/channels/{channel}/messages?limit=100") or []
            if not old:
                break
            for message in old:
                call("DELETE", f"/channels/{channel}/messages/{message['id']}")
        message_ids = [call("POST", f"/channels/{channel}/messages", payload(embed))["id"] for embed in embeds]
        # Links point at ids that only exist now, so each message that carries one is rewritten.
        real_embeds, offsets = layout(intro_title, intro, sections, message_ids, channel)
        for message_id, before, after in zip(message_ids, embeds, real_embeds):
            if before != after:
                call("PATCH", f"/channels/{channel}/messages/{message_id}", payload(after))

    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as file:
        json.dump({"channel": channel, "ids": message_ids}, file)

    index = []
    for section, offset in zip(sections, offsets):
        link = f"https://discord.com/channels/{GUILD}/{channel}/{message_ids[offset]}"
        plain = re.sub(r"\s+", " ", re.sub(r"[*`>#]|\[([^\]]+)\]\([^)]*\)", r"\1", discord_markdown(section.body, {}))).strip()
        index.append(f"- {section.title}: {link}\n  Covers: {plain[:EXCERPT_LENGTH]}")
    with open(INDEX_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(index) + "\n")

    print(f"synced {len(message_ids)} messages in {len(sections)} sections ({'edited in place' if reuse else 'reposted'})", file=sys.stderr)


if __name__ == "__main__":
    main()
