"""FastAPI 主應用"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from api.routes import router
from config.settings import settings
from utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時
    logger.info("🏥 中醫診斷系統啟動中...")
    settings.llm.api_key  # 驗證配置
    logger.info("✅ 系統啟動完成")

    yield

    # 關閉時
    logger.info("👋 系統正在關閉...")

# 創建 FastAPI 應用
app = FastAPI(
    title="中醫螺旋案例推理輔助診斷系統",
    description="TCM Case-Based Reasoning Diagnostic Support System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(router, prefix="/api/v1")

# 健康檢查
@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "service": "TCM-CBR-Agent",
        "version": "1.0.0"
    }

# 根路徑
@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "🏥 中醫螺旋案例推理輔助診斷系統",
        "docs": "/docs",
        "api": "/api/v1"
    }

# 全局異常處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"全局異常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "內部服務器錯誤", "detail": str(exc)}
    )

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )