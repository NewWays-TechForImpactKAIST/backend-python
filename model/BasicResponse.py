from pydantic import BaseModel


SUCCESS = 200
REGION_CODE_ERR = 400
COLLECTION_NOT_EXIST_ERR = 600


class MessageResponse(BaseModel):
    message: str
    code: int = SUCCESS


class ErrorResponse(BaseModel):
    error: str
    code: int
    message: str
