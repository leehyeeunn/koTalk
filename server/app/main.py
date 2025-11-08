from fastapi import FastAPI
from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware
from app.config import CORS_ORIGINS
from app.routers import health, stt, ipa
from app.services.whisper_svc import load_model

# Lifespan 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ 서버 시작 시 실행
    load_model()
    yield
    # ✅ 서버 종료 시 정리할 작업이 있으면 여기에 작성
    # e.g. close_db(), clear_cache(), release_model()
    print("Server shutting down...")

# 앱 초기화
app = FastAPI(title="Whisper STT Server", version="v1", lifespan=lifespan)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router)
app.include_router(stt.router)
app.include_router(ipa.router)
