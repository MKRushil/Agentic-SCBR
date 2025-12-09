"""系統配置文件 - 支援 Weaviate 向量庫與 NVIDIA API"""
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass
class WeaviateConfig:
    """向量數據庫配置"""
    host: str = os.getenv("WEAVIATE_HOST", "localhost")
    port: int = int(os.getenv("WEAVIATE_PORT", "8080"))
    grpc_port: int = int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))
    api_key: str = os.getenv("WEAVIATE_API_KEY", "key-admin")
    timeout: int = int(os.getenv("WEAVIATE_TIMEOUT", "30"))
    collection_name: str = os.getenv("WEAVIATE_COLLECTION", "TCMCases")
    index_type: str = "hnsw"
    distance_metric: str = "cosine"

    @property
    def url(self):
        """向後兼容的 URL 屬性"""
        return f"http://{self.host}:{self.port}"

@dataclass
class LLMConfig:
    """LLM 配置"""
    api_url: str = os.getenv("LLM_API_URL", "https://integrate.api.nvidia.com/v1")
    api_key: str = os.getenv("LLM_API_KEY", "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")
    model: str = os.getenv("LLM_MODEL", "meta/llama-3.3-70b-instruct")
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "8000"))
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    timeout: float = float(os.getenv("LLM_TIMEOUT", "30"))
    retry: int = int(os.getenv("LLM_RETRY", "2"))

@dataclass
class EmbeddingConfig:
    """嵌入模型配置"""
    api_url: str = os.getenv("EMBEDDING_API_URL", "https://integrate.api.nvidia.com/v1")
    api_key: str = os.getenv("NVIDIA_API_KEY", "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")
    model: str = os.getenv("EMBEDDING_MODEL", "nvidia/nv-embedqa-e5-v5")
    dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
    timeout: float = float(os.getenv("EMBEDDING_TIMEOUT", "30"))
    retry: int = int(os.getenv("EMBEDDING_RETRY", "2"))
    batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

class SystemConfig:
    def __init__(self):
        self.top_k_cases = int(os.getenv("TOP_K_CASES", "5"))
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
        self._base_dir = str(Path(__file__).parent.parent)
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "tcm_cbr_agent.log")
        self.enable_auto_retain = os.getenv("ENABLE_AUTO_RETAIN", "false").lower() == "true"
        self.require_expert_review = os.getenv("REQUIRE_EXPERT_REVIEW", "true").lower() == "true"
        self.use_vector_search = os.getenv("USE_VECTOR_SEARCH", "true").lower() == "true"
        self.use_hybrid_search = os.getenv("USE_HYBRID_SEARCH", "true").lower() == "true"

    @property
    def base_dir(self):
        return self._base_dir

    @property
    def data_dir(self):
        return os.path.join(self._base_dir, "data")

    @property
    def case_library_path(self):
        return os.path.join(self.data_dir, "cases", "case_library.json")

class Settings:
    def __init__(self):
        self.weaviate = WeaviateConfig()
        self.llm = LLMConfig()
        self.embedding = EmbeddingConfig()
        self.system = SystemConfig()

    @property
    def LLM_API_KEY(self):
        return self.llm.api_key

    @property
    def LLM_API_BASE(self):
        return self.llm.api_url

    @property
    def LLM_MODEL(self):
        return self.llm.model

    @property
    def TEMPERATURE(self):
        return self.llm.temperature

    @property
    def MAX_TOKENS(self):
        return self.llm.max_tokens

    @property
    def TOP_K_CASES(self):
        return self.system.top_k_cases

    @property
    def SIMILARITY_THRESHOLD(self):
        return self.system.similarity_threshold

    @property
    def BASE_DIR(self):
        return self.system.base_dir

    @property
    def DATA_DIR(self):
        return self.system.data_dir

    @property
    def CASE_LIBRARY_PATH(self):
        return self.system.case_library_path

    @property
    def LOG_LEVEL(self):
        return self.system.log_level

settings = Settings()
