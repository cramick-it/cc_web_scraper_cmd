from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Dict

class Page(BaseModel):
    site_id: str
    url: str
    status_code: int
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    links: List[Dict] = []
    timestamp: datetime = datetime.now()
    error: Optional[str] = None
    meta: Dict = {}
    processed: bool = True