from __future__ import annotations

import re

# 254 is the longest address mail servers accept (RFC 5321).
CONTACT_FIELD_LIMITS = {"name": 100, "email": 254, "message": 5000}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_MISSING_MESSAGES = {
    "name": "Enter your name.",
    "email": "Enter your email address.",
    "message": "Enter a message.",
}


def clean_contact_values(name: str, email: str, message: str) -> dict[str, str]:
    return {"name": name.strip(), "email": email.strip(), "message": message.strip()}


def validate_contact(values: dict[str, str]) -> dict[str, str]:
    """Return one error message per invalid field, keyed by field name."""
    errors: dict[str, str] = {}
    for field, limit in CONTACT_FIELD_LIMITS.items():
        value = values.get(field, "")
        if not value:
            errors[field] = _MISSING_MESSAGES[field]
        elif len(value) > limit:
            errors[field] = f"{field.capitalize()} must be {limit} characters or fewer."
    if "email" not in errors and not EMAIL_PATTERN.match(values["email"]):
        errors["email"] = "Enter a valid email address."
    return errors
