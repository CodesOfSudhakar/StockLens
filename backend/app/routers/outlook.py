from fastapi import APIRouter, Depends

from ..agents.graph import run_pipeline
from ..deps import Credentials, get_credentials
from ..schemas import Outlook, OutlookRequest

router = APIRouter(prefix="/outlook", tags=["outlook"])


@router.post("/run", response_model=Outlook)
def run(
    body: OutlookRequest,
    creds: Credentials = Depends(get_credentials),
) -> Outlook:
    result = run_pipeline(creds, body.symbol.upper())
    return Outlook(**result)
