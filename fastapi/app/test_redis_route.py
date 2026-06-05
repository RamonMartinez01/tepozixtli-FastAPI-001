# /tepozixtli/fastapi/app/test_redis_route.py 
from fastapi import APIRouter
from redis.asyncio import Redis
import os

router = APIRouter(prefix="/test", tags=["test"])

@router.get("/redis")
async def test_redis():
    try:
        redis_client = Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
        await redis_client.set("test:ping", "pong")
        value = await redis_client.get("test:ping")
        await redis_client.close()
        return {"status": "ok", "redis_value": value}
    except Exception as e:
        return {"status": "error", "message": str(e)}
