"""Stack Configs."""

from typing import Annotated

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application settings"""

    name: str = "stac-fastapi-geoparquet-examples"
    owner: str = "gadomski"
    project: str = "labs"
    release: str = "dev"

    bucket_name: str = "stac-geoparquet-examples"
    collections_key: str = "collections.json"

    timeout: int = 30
    memory: int = 3009
    max_concurrent: int | None = None
    rate_limit: Annotated[
        int | None,
        "maximum average requests per second over an extended period of time",
    ] = 50

    @property
    def stack_name(self) -> str:
        """Generate consistent resource prefix."""
        return self.name

    @property
    def tags(self) -> dict[str, str]:
        """Generate consistent tags for resources."""
        return {
            "Project": self.project,
            "Owner": self.owner,
            "Name": self.name,
            "Release": self.release,
        }

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "STACK_"
