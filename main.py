"""
中醫 CBR 診斷系統 - FastAPI 主程序
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
import time
from datetime import datetime

# 導入系統組件
from config.settings import settings
from utils.logger import logger
from agents.cbr_agent import CBRAgent
from knowledge.case_manager import CaseManager

# 創建 FastAPI 應用
app = FastAPI(
    title="中醫 CBR 診斷系統",
    description="基於案例推理的中醫輔助診斷系統",
    version="1.0.0"
)

# CORS 設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化系統組件
cbr_agent = None
case_manager = None

@app.on_event("startup")
async def startup_event():
    """系統啟動初始化"""
    global cbr_agent, case_manager

    logger.info("="*60)
    logger.info("中醫 CBR 診斷系統正在啟動...")
    logger.info("="*60)

    try:
        # 初始化案例管理器
        case_manager = CaseManager()
        logger.info(f"✅ 案例管理器初始化成功 (案例數: {case_manager.get_case_count()})")

        # 初始化 CBR Agent
        cbr_agent = CBRAgent()
        logger.info("✅ CBR Agent 初始化成功")

        logger.info("="*60)
        logger.info("🚀 系統啟動完成!")
        logger.info(f"📍 API 地址: http://localhost:8000")
        logger.info(f"📖 API 文檔: http://localhost:8000/docs")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"❌ 系統啟動失敗: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """系統關閉清理"""
    logger.info("系統正在關閉...")
    if cbr_agent:
        cbr_agent.close()
    logger.info("✅ 系統已關閉")

# ==================== 數據模型 ====================

class PatientInfo(BaseModel):
    """患者信息"""
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_history: Optional[str] = None

class TongueInfo(BaseModel):
    """舌診信息"""
    color: str = Field(..., description="舌色 (如: 淡紅、紅、暗紅)")
    coating: str = Field(..., description="苔質 (如: 薄白、黃膩、厚膩)")

class DiagnosisQuery(BaseModel):
    """診斷查詢請求"""
    patient_info: Optional[PatientInfo] = None
    chief_complaint: str = Field(..., description="主訴")
    symptoms: List[str] = Field(..., description="症狀列表")
    tongue: TongueInfo = Field(..., description="舌診")
    pulse: str = Field(..., description="脈象")

class ExpertFeedback(BaseModel):
    """專家反饋"""
    approved: bool = Field(..., description="是否批准")
    syndrome: str
    treatment_principle: str
    formula: str
    herbs: List[str]
    modifications: Optional[str] = None
    comments: Optional[str] = None

class ReviewRequest(BaseModel):
    """審核請求"""
    query_id: str
    expert_feedback: ExpertFeedback
    retain_case: bool = Field(default=False, description="是否保留為案例")

# ==================== API 端點 ====================

@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "中醫 CBR 診斷系統 API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "cbr_agent": cbr_agent is not None,
            "case_manager": case_manager is not None
        }
    }

@app.get("/system/status")
async def system_status():
    """系統狀態"""
    try:
        # 獲取 Weaviate 狀態
        weaviate_status = {
            "connected": False,
            "case_count": 0,
            "collection": settings.weaviate.collection_name
        }

        if cbr_agent and cbr_agent.retriever.vector_store:
            try:
                weaviate_status["connected"] = True
                weaviate_status["case_count"] = cbr_agent.retriever.vector_store.get_case_count()
            except:
                pass

        return {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "case_library": {
                "size": case_manager.get_case_count() if case_manager else 0
            },
            "weaviate": weaviate_status,
            "settings": {
                "llm_model": settings.llm.model,
                "embedding_model": settings.embedding.model,
                "top_k_cases": settings.system.top_k_cases
            }
        }
    except Exception as e:
        logger.error(f"獲取系統狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/diagnose")
async def diagnose(query: DiagnosisQuery):
    """執行中醫診斷"""
    if not cbr_agent:
        raise HTTPException(status_code=503, detail="CBR Agent 未初始化")

    start_time = time.time()

    try:
        logger.info("="*60)
        logger.info("收到診斷請求")
        logger.info(f"主訴: {query.chief_complaint}")
        logger.info(f"症狀: {', '.join(query.symptoms)}")
        logger.info("="*60)

        # 轉換為字典格式
        query_dict = {
            "patient_info": query.patient_info.model_dump() if query.patient_info else {},
            "chief_complaint": query.chief_complaint,
            "symptoms": query.symptoms,
            "tongue": query.tongue.model_dump(),
            "pulse": query.pulse
        }

        # 執行診斷
        result = cbr_agent.diagnose(query_dict)

        # 添加元數據
        result["query_id"] = f"Q{int(time.time())}"
        result["timestamp"] = datetime.now().isoformat()
        result["response_time"] = round(time.time() - start_time, 2)

        logger.info(f"✅ 診斷完成 (耗時: {result['response_time']}秒)")
        logger.info(f"證型: {result.get('syndrome', 'N/A')}")
        logger.info("="*60)

        return result

    except Exception as e:
        logger.error(f"❌ 診斷失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"診斷失敗: {str(e)}")

@app.post("/review")
async def review_case(review: ReviewRequest):
    """專家審核案例"""
    if not cbr_agent or not case_manager:
        raise HTTPException(status_code=503, detail="系統組件未初始化")

    try:
        logger.info(f"收到審核請求: {review.query_id}")

        result = {
            "query_id": review.query_id,
            "approved": review.expert_feedback.approved,
            "timestamp": datetime.now().isoformat()
        }

        # 如果需要保留案例
        if review.retain_case and review.expert_feedback.approved:
            # 創建案例對象
            case_data = {
                "case_id": f"CASE_{int(time.time())}",
                "syndrome": review.expert_feedback.syndrome,
                "treatment_principle": review.expert_feedback.treatment_principle,
                "formula": review.expert_feedback.formula,
                "herbs": review.expert_feedback.herbs,
                "efficacy_score": 0.85,  # 默認評分
                "expert_reviewed": True,
                "created_at": datetime.now().isoformat()
            }

            # 保存案例
            case_manager.add_case(case_data)
            result["case_retained"] = True
            result["case_id"] = case_data["case_id"]

            logger.info(f"✅ 案例已保留: {case_data['case_id']}")
        else:
            result["case_retained"] = False

        return result

    except Exception as e:
        logger.error(f"審核失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cases/search")
async def search_cases(criteria: Dict[str, Any]):
    """搜索案例"""
    if not case_manager:
        raise HTTPException(status_code=503, detail="案例管理器未初始化")

    try:
        # 使用案例管理器搜索
        cases = case_manager.search_cases(criteria)
        return cases

    except Exception as e:
        logger.error(f"案例搜索失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_statistics():
    """獲取系統統計"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "case_library_size": case_manager.get_case_count() if case_manager else 0,
            "vector_store_size": 0,
            "total_queries": 0,  # 可以從日誌或數據庫獲取
            "avg_response_time": 0.0
        }

        # 獲取向量庫統計
        if cbr_agent and cbr_agent.retriever.vector_store:
            try:
                stats["vector_store_size"] = cbr_agent.retriever.vector_store.get_case_count()
            except:
                pass

        return stats

    except Exception as e:
        logger.error(f"獲取統計失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cases/{case_id}")
async def get_case(case_id: str):
    """獲取特定案例"""
    if not case_manager:
        raise HTTPException(status_code=503, detail="案例管理器未初始化")

    try:
        case = case_manager.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"案例 {case_id} 不存在")
        return case

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取案例失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 主程序入口 ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )