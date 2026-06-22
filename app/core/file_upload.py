from werkzeug.datastructures import FileStorage

from app.errors import UnsupportedFileError, ValidationError

ALLOWED_EXTENSIONS = (".log", ".txt")


def read_log_file(uploaded_file: FileStorage | None) -> str:
    if uploaded_file is None or not uploaded_file.filename:
        raise ValidationError("A file field named 'file' is required.")
    if not has_allowed_extension(uploaded_file.filename):
        raise UnsupportedFileError("Only .log and .txt files are allowed.")
    content: bytes = uploaded_file.read()
    return content.decode("utf-8", errors="replace")


def has_allowed_extension(filename: str) -> bool:
    return filename.lower().endswith(ALLOWED_EXTENSIONS)
