from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.errors import ValidationError


def validate_payload[ModelT: BaseModel](model: type[ModelT], payload: object) -> ModelT:
    try:
        return model.model_validate(payload)
    except PydanticValidationError as error:
        raise ValidationError("Invalid request data.", details=format_errors(error)) from error


def format_errors(error: PydanticValidationError) -> list[dict[str, str]]:
    return [
        {"field": ".".join(str(part) for part in item["loc"]), "message": item["msg"]}
        for item in error.errors()
    ]
