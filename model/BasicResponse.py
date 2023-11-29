from pydantic import BaseModel


SUCCESS = 200
REGION_CODE_ERR = 400
COLLECTION_NOT_EXIST_ERR = 600
NO_DATA_ERROR = 800


class MessageResponse(BaseModel):
    message: str
    code: int = SUCCESS


class ErrorResponse(BaseModel):
    error: str
    code: int
    message: str


NO_DATA_ERROR_RESPONSE: ErrorResponse = ErrorResponse.model_validate(
    {
        "error": "NoDataError",
        "code": NO_DATA_ERROR,
        "message": "No data was retrieved with the provided input.",
    }
)
