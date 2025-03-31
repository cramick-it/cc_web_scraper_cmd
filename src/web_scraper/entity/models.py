from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return {
            'type': 'objectid',
            'py_type': cls,
        }


class File(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: str
    page_id: PyObjectId = Field(..., alias="page_id")
    title: str
    file_name: str
    file_extension: str
    created_at: datetime = datetime.now()


class Link(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: str
    page_id: PyObjectId = Field(..., alias="page_id")
    title: str
    href: str
    created_at: datetime = datetime.now()


class Heading(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    tag: str
    page_id: PyObjectId = Field(..., alias="page_id")
    title: str
    text: str
    text_html: str
    anchor: str
    level: int
    checksum: str
    parent_id: Optional[PyObjectId] = Field(None, alias="parent_id")
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class Page(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

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
