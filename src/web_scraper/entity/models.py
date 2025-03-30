from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Dict

class Heading(BaseModel):
    tag: str
    title: str
    text: str
    text_html: str
    anchor: str
    level: int
    checksum: str
    created_at: datetime
    updated_at: datetime
    changed_at: datetime

class Page(BaseModel):
    site_id: str
    url: str
    status_code: int
    content_html: Optional[str] = None
    content_text: Optional[str] = None
    headings: List[Heading] = []
    links: List[Dict] = []
    checksum: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    changed_at: datetime = datetime.now()
    error: Optional[str] = None
    processed: bool = True