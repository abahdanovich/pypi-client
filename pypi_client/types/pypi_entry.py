from typing import Dict, List, Optional

from pydantic import BaseModel  # pylint: disable=no-name-in-module


class PypiProjectUrls(BaseModel):
    Source: Optional[str]

class PypiPackageInfo(BaseModel):
    summary: Optional[str]
    version: Optional[str] 
    project_urls: Optional[PypiProjectUrls]
    home_page: Optional[str]

    # @validator('project_urls', pre=True)
    # def ensure_project_urls(cls, val: Any) -> Any:      # pylint: disable=no-self-argument
    #     return val or []

class PypiReleaseUpload(BaseModel):
    upload_time: str

class PypiEntry(BaseModel):
    info: PypiPackageInfo
    releases: Dict[str, List[PypiReleaseUpload]] = {}
