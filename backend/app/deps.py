from dataclasses import dataclass

from fastapi import Header

from .config import get_settings


@dataclass
class Credentials:
    """Per-request credentials, forwarded by the frontend from localStorage.
    Falls back to server-side .env values when a header is missing."""

    angel_client_id: str
    angel_api_key: str
    angel_pin: str
    angel_totp_secret: str
    groq_api_key: str

    @property
    def has_angel(self) -> bool:
        return bool(self.angel_client_id and self.angel_api_key and self.angel_pin)

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)


def get_credentials(
    x_angel_client_id: str | None = Header(default=None),
    x_angel_api_key: str | None = Header(default=None),
    x_angel_pin: str | None = Header(default=None),
    x_angel_totp_secret: str | None = Header(default=None),
    x_groq_api_key: str | None = Header(default=None),
) -> Credentials:
    s = get_settings()
    return Credentials(
        angel_client_id=x_angel_client_id or s.angel_client_id,
        angel_api_key=x_angel_api_key or s.angel_api_key,
        angel_pin=x_angel_pin or s.angel_pin,
        angel_totp_secret=x_angel_totp_secret or s.angel_totp_secret,
        groq_api_key=x_groq_api_key or s.groq_api_key,
    )
