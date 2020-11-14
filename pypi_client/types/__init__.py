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


# Progress bar
Item = TypeVar('Item')
ProgressBar = Callable[[Iterable[Item], int], ContextManager[Iterable[Item]]]


class DeviceFlowVerificationCodes(TypedDict):
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int