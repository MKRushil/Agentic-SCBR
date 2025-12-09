"""Weaviate 向量資料庫管理 - 使用 HOST/PORT 配置"""
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery
from weaviate.auth import AuthApiKey
from typing import List, Dict, Any, Optional
from config.settings import settings
from utils.logger import logger
import json

class WeaviateVectorStore:
    """Weaviate 向量資料庫管理器"""

    def __init__(self):
        self.config = settings.weaviate
        self.client = None
        self.collection = None
        self._connect()

    def _connect(self):
        """連接到 Weaviate"""
        try:
            host = self.config.host
            port = self.config.port
            grpc_port = self.config.grpc_port
            api_key = self.config.api_key

            logger.info(f"正在連接 Weaviate: {host}:{port} (gRPC: {grpc_port})")

            # 準備認證
            auth_config = None
            if api_key:
                auth_config = AuthApiKey(api_key)
                logger.info(f"使用 API Key 認證")

            # 連接 Weaviate
            self.client = weaviate.connect_to_local(
                host=host,
                port=port,
                grpc_port=grpc_port,
                auth_credentials=auth_config
            )

            # 檢查連接
            if self.client.is_ready():
                logger.info(f"✅ Weaviate 連接成功 ({host}:{port})")
                self._init_collection()
            else:
                logger.warning("⚠️  Weaviate 連接建立但服務未就緒")
                self.client = None

        except Exception as e:
            logger.error(f"❌ 連接 Weaviate 失敗: {e}")
            logger.warning("💡 請檢查:")
            logger.warning(f"   1. Weaviate 是否運行: docker ps | grep weaviate")
            logger.warning(f"   2. 端口是否正確: {port} (HTTP), {grpc_port} (gRPC)")
            logger.warning(f"   3. API Key 是否匹配: {api_key}")
            self.client = None

    def _init_collection(self):
        """初始化案例集合"""
        if not self.client:
            return

        try:
            collection_name = self.config.collection_name

            if self.client.collections.exists(collection_name):
                self.collection = self.client.collections.get(collection_name)
                logger.info(f"✅ 載入集合: {collection_name}")
            else:
                self.collection = self.client.collections.create(
                    name=collection_name,
                    description="中醫案例向量庫",
                    vectorizer_config=Configure.Vectorizer.none(),
                    properties=[
                        Property(name="case_id", data_type=DataType.TEXT),
                        Property(name="chief_complaint", data_type=DataType.TEXT),
                        Property(name="symptoms", data_type=DataType.TEXT_ARRAY),
                        Property(name="tongue_color", data_type=DataType.TEXT),
                        Property(name="tongue_coating", data_type=DataType.TEXT),
                        Property(name="pulse", data_type=DataType.TEXT),
                        Property(name="syndrome", data_type=DataType.TEXT),
                        Property(name="treatment_principle", data_type=DataType.TEXT),
                        Property(name="formula", data_type=DataType.TEXT),
                        Property(name="herbs", data_type=DataType.TEXT_ARRAY),
                        Property(name="efficacy_score", data_type=DataType.NUMBER),
                        Property(name="metadata", data_type=DataType.TEXT),
                    ]
                )
                logger.info(f"✅ 創建集合: {collection_name}")

        except Exception as e:
            logger.error(f"❌ 初始化集合失敗: {e}")
            self.collection = None

    def add_case(self, case: Dict[str, Any], vector: List[float]) -> bool:
        if not self.collection:
            return False
        try:
            properties = {
                "case_id": case.get("case_id", ""),
                "chief_complaint": case.get("chief_complaint", ""),
                "symptoms": case.get("symptoms", []),
                "tongue_color": case.get("tongue", {}).get("color", ""),
                "tongue_coating": case.get("tongue", {}).get("coating", ""),
                "pulse": case.get("pulse", ""),
                "syndrome": case.get("syndrome", ""),
                "treatment_principle": case.get("treatment_principle", ""),
                "formula": case.get("formula", ""),
                "herbs": case.get("herbs", []),
                "efficacy_score": float(case.get("efficacy_score", 0)),
                "metadata": json.dumps(case.get("patient_info", {}), ensure_ascii=False)
            }
            uuid = self.collection.data.insert(properties=properties, vector=vector)
            logger.info(f"✅ 添加案例: {case.get('case_id')}")
            return True
        except Exception as e:
            logger.error(f"❌ 添加案例失敗: {e}")
            return False

    def search_similar(self, query_vector: List[float], top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.collection:
            return []
        try:
            response = self.collection.query.near_vector(
                near_vector=query_vector,
                limit=top_k,
                return_metadata=MetadataQuery(distance=True)
            )
            results = []
            for obj in response.objects:
                case_data = {
                    "case_id": obj.properties.get("case_id"),
                    "chief_complaint": obj.properties.get("chief_complaint"),
                    "symptoms": obj.properties.get("symptoms", []),
                    "tongue": {"color": obj.properties.get("tongue_color"), "coating": obj.properties.get("tongue_coating")},
                    "pulse": obj.properties.get("pulse"),
                    "syndrome": obj.properties.get("syndrome"),
                    "treatment_principle": obj.properties.get("treatment_principle"),
                    "formula": obj.properties.get("formula"),
                    "herbs": obj.properties.get("herbs", []),
                    "efficacy_score": obj.properties.get("efficacy_score", 0),
                    "similarity_score": 1 - obj.metadata.distance,
                    "vector_distance": obj.metadata.distance
                }
                results.append(case_data)
            logger.info(f"✅ 搜索到 {len(results)} 個相似案例")
            return results
        except Exception as e:
            logger.error(f"❌ 搜索失敗: {e}")
            return []

    def get_case_count(self) -> int:
        if not self.collection:
            return 0
        try:
            response = self.collection.aggregate.over_all(total_count=True)
            return response.total_count
        except:
            return 0

    def close(self):
        if self.client:
            self.client.close()
            logger.info("Weaviate 連接已關閉")
