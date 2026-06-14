from fastapi import APIRouter, Depends

from ..deps import Credentials, get_credentials
from ..schemas import Overview
from ..services import angel_one

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/overview", response_model=Overview)
def overview(creds: Credentials = Depends(get_credentials)) -> Overview:
    return Overview(**angel_one.get_overview(creds))
