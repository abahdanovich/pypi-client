from typing import Dict

from pydantic import BaseModel  # pylint: disable=no-name-in-module


class PackageStats(BaseModel):
    downloads: Dict[str, Dict[str, int]]
