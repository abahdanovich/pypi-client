from typing import Dict, List, Optional, TypedDict


class PypiProjectUrls(TypedDict):
    Source: Optional[str]

class PypiPackageInfo(TypedDict):
    summary: Optional[str]
    version: Optional[str] 
    project_urls: Optional[PypiProjectUrls]
    home_page: Optional[str]

class PypiReleaseUpload(TypedDict):
    upload_time: str

class PypiEntry(TypedDict):
    info: PypiPackageInfo
    releases: Optional[Dict[str, List[PypiReleaseUpload]]]
