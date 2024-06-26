from typing import Any, Literal

from pas.knowledge.embedder.base import Embedder
from pas.utils.log import logger

try:
    from openai import OpenAI as OpenAIClient
    from openai.types.create_embedding_response import CreateEmbeddingResponse
except ImportError:
    from pas.const import DEPENDENCY_GROUP_OPENAI, IMPORT_ERROR

    logger.error(IMPORT_ERROR("openai", DEPENDENCY_GROUP_OPENAI))
    raise


class OpenAIEmbedder(Embedder):
    model: str = "text-embedding-ada-002"
    dimensions: int = 1536
    encoding_format: Literal["float", "base64"] = "float"
    user: str | None = None
    api_key: str | None = None
    organization: str | None = None
    base_url: str | None = None
    request_params: dict[str, Any] | None = None
    client_params: dict[str, Any] | None = None
    openai_client: OpenAIClient | None = None

    @property
    def client(self) -> OpenAIClient:
        if self.openai_client:
            return self.openai_client

        _client_params: dict[str, Any] = {}
        if self.api_key:
            _client_params["api_key"] = self.api_key
        if self.organization:
            _client_params["organization"] = self.organization
        if self.base_url:
            _client_params["base_url"] = self.base_url
        if self.client_params:
            _client_params.update(self.client_params)
        return OpenAIClient(**_client_params)

    def _response(self, text: str) -> CreateEmbeddingResponse:
        _request_params: dict[str, Any] = {
            "input": text,
            "model": self.model,
            "encoding_format": self.encoding_format,
        }
        if self.user is not None:
            _request_params["user"] = self.user
        if self.model.startswith("text-embedding-3"):
            _request_params["dimensions"] = self.dimensions
        if self.request_params:
            _request_params.update(self.request_params)
        return self.client.embeddings.create(**_request_params)

    def get_embedding(self, text: str) -> list[float]:
        response: CreateEmbeddingResponse = self._response(text=text)
        try:
            return response.data[0].embedding
        except Exception as e:
            logger.warning(e)
            return []

    def get_embedding_and_usage(self, text: str) -> tuple[list[float], dict | None]:
        response: CreateEmbeddingResponse = self._response(text=text)

        embedding = response.data[0].embedding
        usage = response.usage
        return embedding, usage.model_dump()
