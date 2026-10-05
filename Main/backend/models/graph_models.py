from pydantic import BaseModel
from typing import Dict, Any


class CreateNodeRequest(BaseModel):
    label: str
    properties: Dict[str, Any]