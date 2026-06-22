import re

from pydantic import ValidationError

from app.schemas.log import LineError, LogEntryInput

LOG_LINE_PATTERN = re.compile(
    r"^(?P<timestamp>\S+)\s+(?P<level>\S+)\s+(?P<source>\S+)\s+(?P<message>.+)$"
)


def parse_log_content(content: str) -> tuple[list[LogEntryInput], list[LineError]]:
    entries: list[LogEntryInput] = []
    errors: list[LineError] = []

    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        fields = match_log_line(line)
        if fields is None:
            errors.append(LineError(line=line_number, reason="malformed log line"))
            continue

        try:
            entries.append(LogEntryInput.model_validate(fields))
        except ValidationError:
            errors.append(LineError(line=line_number, reason="invalid log entry"))

    return entries, errors


def match_log_line(line: str) -> dict[str, str] | None:
    match = LOG_LINE_PATTERN.match(line)
    if match is None:
        return None
    return match.groupdict()
