from pydantic import HttpUrl, TypeAdapter, ValidationError

_http_url_adapter = TypeAdapter(HttpUrl)


def normalize_http_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    try:
        return str(_http_url_adapter.validate_python(value))
    except ValidationError:
        return None
