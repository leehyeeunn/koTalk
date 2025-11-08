from fastapi import APIRouter
from pydantic import BaseModel
from app.utils.ipa_converter import text_to_ipa

router = APIRouter(prefix="/ipa", tags=["IPA"])

class IpaRequest(BaseModel):
    text: str

@router.post("/")
def convert_ipa(req: IpaRequest):
    result = text_to_ipa(req.text)
    return result
