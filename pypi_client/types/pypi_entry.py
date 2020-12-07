from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel  # pylint: disable=no-name-in-module

Url = str


class PypiProjectUrls(BaseModel):
    Source: Optional[Url]


class PypiPackageInfo(BaseModel):
    name: str
    summary: Optional[str]
    version: Optional[str]
    project_urls: Optional[PypiProjectUrls]
    home_page: Optional[Url]

    # @validator('project_urls', pre=True)
    # def ensure_project_urls(cls, val: Any) -> Any:      # pylint: disable=no-self-argument
    #     return val or []


class PypiReleaseUpload(BaseModel):
    upload_time: datetime


Version = str


class PypiEntry(BaseModel):
    info: PypiPackageInfo
    releases: Dict[Version, List[PypiReleaseUpload]] = {}
