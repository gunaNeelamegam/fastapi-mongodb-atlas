from typing import Annotated
from config.settings import Settings, settings
from fastapi import Depends,APIRouter

bare_router = APIRouter()

@bare_router.get("/")
def home(setting: Annotated[Settings, None] = Depends(settings)):
    return {
        "message": "auth application",
        "api-version": setting.api_version
    }

__annotations__ = (bare_router)
