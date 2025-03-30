from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Dict

class Heading(BaseModel):
    tag: str
    text: str
    anchor: str
    level: int
    checksum: str

class Page(BaseModel):
    site_id: str
    url: str
    status_code: int
    content_html: Optional[str] = None
    content_text: Optional[str] = None
    headings: List[Heading] = []
    links: List[Dict] = []
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    checksum: Optional[str] = None
    error: Optional[str] = None
    processed: bool = True