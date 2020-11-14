from typing import Dict, TypedDict


class PackageStats(TypedDict):
    downloads: Dict[str, Dict[str, int]]
