from fastapi import APIRouter

health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("")
async def check_health():
    return {"details": "Conectado à API."}
