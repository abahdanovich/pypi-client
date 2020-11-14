from dataclasses import dataclass
from typing import (Callable, ContextManager, Dict, Iterable, List, Optional,
                    TypedDict, TypeVar)


@dataclass
class Package:
    name: str
    summary: Optional[str] = None
    version: Optional[str] = None
    home_page: Optional[str] = None
    downloads: Optional[int] = None
    stars: Optional[int] = None
    releases: Optional[int] = None
    last_release_date: Optional[str] = None
    score: Optional[int] = None


class PypiProjectUrls(TypedDict):
    Source: Optional[str]

class PypiPackageInfo(TypedDict):
    summary: Optional[str]
    version: Optional[str] 
    project_urls: Optional[PypiProjectUrls]
    home_page: Optional[str]

class PypiReleaseUpload(TypedDict):
    upload_time: Optional[str]

class PypiEntry(TypedDict):
    info: Optional[PypiPackageInfo]
    releases: Optional[Dict[str, List[PypiReleaseUpload]]]


class GithubRepo(TypedDict):
    stargazers_count: Optional[int]


# Progress bar
Item = TypeVar('Item')
ProgressBar = Callable[[Iterable[Item], int], ContextManager[Iterable[Item]]]
