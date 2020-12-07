from typing import Callable, ContextManager, Iterable, Optional, TypeVar

from pydantic import BaseModel  # pylint: disable=no-name-in-module


class Package(BaseModel):
    name: str
    summary: Optional[str]
    version: Optional[str]
    home_page: Optional[str]
    downloads: Optional[int]
    stars: Optional[int]
    releases: Optional[int]
    last_release_date: Optional[str]
    score: Optional[int]


# Progress bar
Item = TypeVar('Item')
ProgressBar = Callable[[Iterable[Item], int], ContextManager[Iterable[Item]]]


class DeviceFlowVerificationCodes(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


class AccessToken(BaseModel):
    access_token: str
