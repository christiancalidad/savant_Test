from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.voice import router as voice_router
from app.config import settings

app = FastAPI(title=settings.app_name)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(voice_router)
