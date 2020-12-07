from datetime import date
from typing import Dict

from pydantic import BaseModel  # pylint: disable=no-name-in-module

Version = str


class PackageStats(BaseModel):
    downloads: Dict[date, Dict[Version, int]]
