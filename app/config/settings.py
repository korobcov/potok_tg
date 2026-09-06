from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_ID: Union[List[int], int, str]
    CHANNEL_ID: Union[int, str]
    # HTTP(S) proxy for the Telegram Bot API, e.g. "http://user:pass@host:port".
    # Needed when api.telegram.org is blocked/unreachable directly (common
    # with some ISPs), while the Telegram app itself still works.
    PROXY_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("ADMIN_ID", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Union[int, str, List[int]]) -> List[int]:
        if isinstance(v, int):
            return [v]
        if isinstance(v, list):
            return [int(x) for x in v]
        if isinstance(v, str):
            # Parse comma-separated string like "123, 456"
            return [
                int(x.strip()) for x in v.split(",") if x.strip().isdigit()
            ]
        raise ValueError(f"Invalid ADMIN_ID format: {v}")


settings = Settings()
