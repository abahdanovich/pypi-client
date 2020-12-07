from pydantic import BaseModel  # pylint: disable=no-name-in-module


class GithubRepo(BaseModel):
    stargazers_count: int
