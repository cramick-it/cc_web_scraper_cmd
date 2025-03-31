from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Dict
from bson import ObjectId

class File(BaseModel):
    url: str
    page_id: ObjectId
    title: str
    file_name: str
    file_extension: str
    created_at: datetime = datetime.now()

class Link(BaseModel):
    url: str
    page_id: ObjectId
    title: str
    href: str
    created_at: datetime = datetime.now()

class Heading(BaseModel):
    tag: str
    page_id: ObjectId
    title: str
    text: str
    text_html: str
    anchor: str
    level: int
    checksum: str
    parent_id: Optional[ObjectId] = None  # For nested headings
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class Page(BaseModel):
    site_id: str
    url: str
    status_code: int
    content_html: Optional[str] = None
    content_text: Optional[str] = None
    checksum: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    error: Optional[str] = None
    processed: bool = True