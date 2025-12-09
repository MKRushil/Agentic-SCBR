"""API 路由定義"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from workflow.pipeline import TCMDiagnosisPipeline
from knowledge.case_database import CaseDatabase
from utils.logger import logger

router = APIRouter()

# 全局診斷管線實例
pipeline = TCMDiagnosisPipeline()
case_db = CaseDatabase()

# ==================== 請求/響應模型 ====================

class PatientInfo(BaseModel):
    """患者基本信息"""
    age: Optional[int] = Field(None, ge=0, le=150, description="年齡")
    gender: Optional[str] = Field(None, pattern="^(男|女)$", description="性別")

class DiagnosisRequest(BaseModel):
    """診斷請求"""
    patient_input: str = Field(..., min_length=10, description="患者症狀描述（包含主訴、症狀、舌脈等）")
    patient_info: Optional[PatientInfo] = Field(None, description="患者基本信息")

    class Config:
        json_schema_extra = {
            "example": {
                "patient_input": "患者女性,45歲,主訴頭暈乏力2月餘。症狀:頭暈目眩,心悸失眠,面色蒼白,神疲乏力,月經量少色淡。舌象:舌淡苔薄白。脈象:脈細弱。",
                "patient_info": {
                    "age": 45,
                    "gender": "女"
                }
            }
        }

class DiagnosisResponse(BaseModel):
    """診斷響應"""
    status: str
    diagnosis: Dict[str, Any]
    explanation: str
    similar_cases: list
    confidence: float
    metadata: Dict[str, Any]

class CaseQueryRequest(BaseModel):
    """案例查詢請求"""
    syndrome: Optional[str] = Field(None, description="證型")
    symptoms: Optional[list] = Field(None, description="症狀列表")
    limit: int = Field(10, ge=1, le=50, description="返回數量")

# ==================== API 端點 ====================

@router.post("/diagnose", response_model=DiagnosisResponse, summary="中醫診斷")
async def diagnose(request: DiagnosisRequest):
    """
    執行中醫診斷

    完整流程:
    1. 觀測 - 提取四診信息
    2. 病機分析 - 推斷病因病機
    3. 聯想案例 - 檢索相似病例
    4. 衝突檢測 - 發現矛盾
    5. 修正判斷 - 調整方案
    6. 辨證論治 - 綜合決策
    7. 生成解釋 - 理法方藥說明
    """
    try:
        logger.info(f"收到診斷請求: {request.patient_input[:50]}...")

        # 準備患者信息
        patient_info = None
        if request.patient_info:
            patient_info = request.patient_info.model_dump()

        # 執行診斷
        result = pipeline.diagnose(
            patient_input=request.patient_input,
            patient_info=patient_info
        )

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))

        # 構建響應
        response = {
            "status": "success",
            "diagnosis": result.get("diagnosis", {}),
            "explanation": result.get("explanation", ""),
            "similar_cases": result.get("top_similar_cases", []),
            "confidence": result.get("diagnosis", {}).get("confidence", 0),
            "metadata": {
                "conflicts_detected": result.get("conflicts_detected", 0),
                "similar_cases_count": result.get("similar_cases_count", 0),
                "pathogenesis": result.get("pathogenesis_analysis", {})
            }
        }

        logger.info(f"診斷完成: {response['diagnosis'].get('main_syndrome', 'Unknown')}")
        return response

    except Exception as e:
        logger.error(f"診斷失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"診斷失敗: {str(e)}")

@router.get("/cases", summary="查詢案例庫")
async def get_cases(
    syndrome: Optional[str] = None,
    limit: int = 10
):
    """
    查詢案例庫

    可根據證型篩選,返回案例列表
    """
    try:
        if syndrome:
            cases = case_db.search_by_syndrome(syndrome)
        else:
            cases = case_db.get_all_cases()

        # 限制返回數量
        cases = cases[:limit]

        return {
            "status": "success",
            "total": len(cases),
            "cases": cases
        }
    except Exception as e:
        logger.error(f"查詢案例失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cases/{case_id}", summary="獲取單個案例")
async def get_case(case_id: str):
    """根據案例ID獲取詳細信息"""
    try:
        case = case_db.get_case_by_id(case_id)

        if not case:
            raise HTTPException(status_code=404, detail=f"案例 {case_id} 不存在")

        return {
            "status": "success",
            "case": case
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取案例失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics", summary="案例庫統計")
async def get_statistics():
    """獲取案例庫統計信息"""
    try:
        stats = case_db.get_statistics()

        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"獲取統計失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cases/search", summary="搜索相似案例")
async def search_cases(
    chief_complaint: str,
    symptoms: list,
    limit: int = 5
):
    """
    根據症狀搜索相似案例
    """
    try:
        cases = case_db.search_by_symptoms(symptoms)
        cases = cases[:limit]

        return {
            "status": "success",
            "total": len(cases),
            "cases": cases
        }
    except Exception as e:
        logger.error(f"搜索失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/syndromes", summary="獲取證型列表")
async def get_syndromes():
    """獲取所有證型列表"""
    try:
        from config.settings import settings
        from utils.json_handler import JSONHandler
        from pathlib import Path

        knowledge_path = Path(__file__).parent.parent / 'config' / 'tcm_knowledge.json'
        knowledge = JSONHandler.load_json(str(knowledge_path))

        syndromes = knowledge.get('syndromes', {})

        syndrome_list = [
            {
                "name": name,
                "treatment_principle": info.get("treatment_principle", ""),
                "key_symptoms": info.get("key_symptoms", [])
            }
            for name, info in syndromes.items()
        ]

        return {
            "status": "success",
            "total": len(syndrome_list),
            "syndromes": syndrome_list
        }
    except Exception as e:
        logger.error(f"獲取證型列表失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config", summary="獲取系統配置")
async def get_config():
    """獲取系統配置信息（隱藏敏感信息）"""
    from config.settings import settings

    return {
        "status": "success",
        "config": {
            "llm_model": settings.llm.model,
            "embedding_model": settings.embedding.model,
            "embedding_dimension": settings.embedding.dimension,
            "top_k_cases": settings.system.top_k_cases,
            "similarity_threshold": settings.system.similarity_threshold,
            "use_vector_search": settings.system.use_vector_search,
            "weaviate_url": settings.weaviate.url,
            "weaviate_collection": settings.weaviate.collection_name
        }
    }