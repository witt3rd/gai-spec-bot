import datetime
import json
import os

from dotenv import load_dotenv
from pydantic import BaseModel
import snakemd
from snakemd import Inline, Paragraph, Raw

from config import get_config

#
# Models
#


class Message(BaseModel):
    speaker: str
    message: str

    def __str__(self) -> str:
        return f"### {self.speaker}: {self.message}"


class Session(BaseModel):
    name: str
    timestamp: str
    scenario: str
    red_bot: str
    red_directive: str
    blue_bot: str
    blue_directive: str
    first_speaker: str
    prompt: str
    tokens: int = 0
    cost: float = 0.0
    messages: list[Message] = []


#
# Functions
#


def _mk_session_filename(name: str, dir: str) -> str:
    session_file = os.path.join(dir, f"{name}.json")
    return session_file


def session_save(session: Session, session_dir: str) -> None:
    os.makedirs(session_dir, exist_ok=True)
    session_file = _mk_session_filename(session.name, session_dir)
    with open(session_file, "w") as f:
        json.dump(session.dict(), f, indent=2)


def session_dir(session_dir: str) -> list[str]:
    os.makedirs(session_dir, exist_ok=True)
    sessions = []
    for file in os.listdir(session_dir):
        if file.endswith(".json"):
            sessions.append(file.removesuffix(".json"))
    return sessions


def session_prune(session_dir: str, exclude: Session) -> None:
    for file in os.listdir(session_dir):
        if file.endswith(".json"):
            filename = file.removesuffix(".json")
            if filename != exclude.name:
                session = Session.parse_file(os.path.join(session_dir, file))
                if len(session.messages) < 2:
                    os.remove(os.path.join(session_dir, file))


def session_load(name: str, session_dir: str) -> Session:
    session_file = _mk_session_filename(name, session_dir)
    session = Session.parse_file(session_file)
    return session


def _mk_transcript_filename(
    dir: str,
    name: str,
    timestamp: str,
) -> str:
    # ensure outdir exists
    os.makedirs(dir, exist_ok=True)
    transcript_file = os.path.join(dir, f"{name} {timestamp}")
    return transcript_file


def session_transcript_save(
    session: Session,
    dir: str,
) -> None:
    transcript_file = _mk_transcript_filename(
        dir,
        session.name,
        session.timestamp,
    )

    # parse the timestamp
    print(f"timestamp: {session.timestamp}")
    timestamp = datetime.datetime.strptime(
        session.timestamp,
        get_config().DATETIME_FORMAT,
    )

    doc = snakemd.new_doc()
    doc.add_heading(session.name, 1)
    doc.add_paragraph(
        f"A Red v Blue transcript between {session.red_bot} (red) and {session.blue_bot} (blue) on {timestamp.strftime('%B %d, %Y at %I:%M %p')}."
    )

    doc.add_heading(f"Directives", 2)

    doc.add_heading(f"{session.red_bot} (Red)", 3)
    doc.add_paragraph(session.red_directive)

    doc.add_heading(f"{session.blue_bot} (Blue)", 3)
    doc.add_paragraph(session.blue_directive)

    doc.add_heading(f"Discussion", 2)
    speakers = {
        "Red": session.red_bot,
        "Blue": session.blue_bot,
    }
    for message in session.messages:
        doc.add_block(Inline(f"{speakers[message.speaker]}:", bold=True))
        doc.add_raw(message.message)
    doc.dump(transcript_file)


def session_transcript_load(
    dir: str,
    name: str,
    timestamp: str,
) -> str | None:
    transcript_file = (
        _mk_transcript_filename(
            dir,
            name,
            timestamp,
        )
        + ".md"
    )
    # does the file exist?
    if not os.path.exists(transcript_file):
        return None
    with open(transcript_file, "r") as f:
        transcript = f.read()
    return transcript
