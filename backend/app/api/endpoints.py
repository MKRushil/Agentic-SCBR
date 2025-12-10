from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from app.api.schemas import ChatRequest, ChatResponse, FeedbackRequest
from app.core.orchestrator import Orchestrator
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# 取得單例 Orchestrator
orchestrator = Orchestrator()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    核心對話接口
    觸發 Orchestrator 的序列化管線。
    """
    logger.info(f"[API] Received chat request for Session: {request.session_id}")
    
    try:
        # 調用 Orchestrator，傳入 background_tasks 用於 Summarization
        response = await orchestrator.process_session(request, background_tasks)
        return response
    
    except ValueError as ve:
        # 輸入防禦攔截到的錯誤 (如 Injection)
        logger.warning(f"[API] Input validation failed: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
        
    except Exception as e:
        logger.error(f"[API] Internal Server Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="系統內部錯誤，請稍後再試。"
        )

@router.post("/feedback")
async def feedback_endpoint(request: FeedbackRequest):
    """
    規格書 7.3 學習閉環
    """
    logger.info(f"[API] Feedback received: {request.action} for Session: {request.session_id}")
    
    try:
        if request.action == "ACCEPT":
            # 觸發寫入 Weaviate (Learned Case)
            # await orchestrator.learn_from_session(request.session_id)
            pass
        elif request.action == "MODIFY":
            # 處理修改後寫入
            pass
            
        return {"status": "success", "message": "Feedback processed"}
        
    except Exception as e:
        logger.error(f"[API] Feedback processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Feedback processing failed")

@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "v8.0"}