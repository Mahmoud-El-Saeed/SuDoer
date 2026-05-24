from __future__ import annotations
import pathlib

from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.enums.model_provider import ModelProvider

class LlmSettings(BaseModel):
    """Summarize LLM provider configuration."""

    provider: ModelProvider
    name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None


class EmbeddingSettings(BaseModel):
    """Summarize embedding provider configuration."""

    provider: ModelProvider
    name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    dimension: int


class PortSettings(BaseModel):
    """Summarize daemon port configuration."""

    daemon_http: int
    daemon_ws: int


class PathSettings(BaseModel):
    """Summarize project path configuration."""

    data_dir: str
    sqlite_path: str
    qdrant_url: str


class Settings(BaseSettings):
    """Summarize runtime settings loaded from env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: ModelProvider = Field(
        default=ModelProvider.openai, validation_alias="LLM_MODEL_PROVIDER"
    )
    llm_model_name_planner: str = Field(
        default="gpt-4o-mini", validation_alias="LLM_MODEL_NAME_PLANER"
    )
    llm_model_name_validator: str = Field(
        default="gpt-4o-mini", validation_alias="LLM_MODEL_NAME_VALIDATOR"
    )
    llm_base_url: Optional[str] = Field(default=None, validation_alias="LLM_BASE_URL")
    llm_api_key: Optional[str] = Field(default=None, validation_alias="LLM_API_KEY")
    embedding_provider: ModelProvider = Field(
        default=ModelProvider.openai, validation_alias="EMBEDDING_PROVIDER"
    )
    embedding_model_name: str = Field(
        default="text-embedding-3-small", validation_alias="EMBEDDING_MODEL_NAME"
    )
    embedding_api_key: Optional[str] = Field(
        default=None, validation_alias="EMBEDDING_API_KEY"
    )
    embedding_base_url: Optional[str] = Field(
        default=None, validation_alias="EMBEDDING_BASE_URL"
    )
    embedding_dimension: int = Field(
        default=1536, validation_alias="EMBEDDING_DIMENSION"
    )
    daemon_http_port: int = Field(default=8000, validation_alias="DAEMON_HTTP_PORT")
    daemon_ws_port: int = Field(default=8001, validation_alias="DAEMON_WS_PORT")
    data_dir_name: str = Field(default="data", validation_alias="DATA_DIR_NAME")
    sqlite_path_name: str = Field(
        default="sudoer.db", validation_alias="SQLITE_PATH_NAME"
    )
    qdrant_url: str = Field(
        default="http://localhost:6333", validation_alias="QDRANT_URL"
    )

    def llm_settings(self, model_name: str) -> LlmSettings:
        """Summarize resolved LLM settings for a named model."""

        return LlmSettings(
            provider=self.llm_provider,
            name=model_name,
            base_url=self.llm_base_url,
            api_key=self.llm_api_key,
        )

    def planner_llm_settings(self) -> LlmSettings:
        """Summarize resolved LLM planner settings."""

        return self.llm_settings(self.llm_model_name_planner)

    def validator_llm_settings(self) -> LlmSettings:
        """Summarize resolved LLM validator settings."""

        return self.llm_settings(self.llm_model_name_validator)

    def embedding_settings(self) -> EmbeddingSettings:
        """Summarize resolved embedding settings."""

        return EmbeddingSettings(
            provider=self.embedding_provider,
            name=self.embedding_model_name,
            base_url=self.embedding_base_url,
            api_key=self.embedding_api_key,
            dimension=self.embedding_dimension,
        )

    def port_settings(self) -> PortSettings:
        """Summarize resolved port settings."""

        return PortSettings(
            daemon_http=self.daemon_http_port,
            daemon_ws=self.daemon_ws_port,
        )

    def path_settings(self) -> PathSettings:
        """Summarize resolved path settings."""
        file_path = pathlib.Path(__file__).parent.parent.parent.resolve()
        data_dir_path = pathlib.Path(file_path, self.data_dir_name).resolve()
        sqlite_path = pathlib.Path(data_dir_path, self.sqlite_path_name).resolve()
        return PathSettings(
            data_dir=str(data_dir_path),
            sqlite_path=str(sqlite_path),
            qdrant_url=self.qdrant_url,
        )
