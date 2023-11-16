from pydantic import BaseModel, Field
from enum import StrEnum

class CouncilType(StrEnum):
    local_council = "local_council"
    national_council = "national_council"
    metropolitan_council = "metropolitan_council"
    local_leader= "local_leader"
    metro_leader = "metro_leader"

class CouncilInfo(BaseModel):
    name : str
    party: str

class ScrapResult(BaseModel):
    council_id : str
    council_type : CouncilType
    councilers : list[CouncilInfo]