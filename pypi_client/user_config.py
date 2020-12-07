from pathlib import Path

from appdirs import user_config_dir

config_dir = Path(user_config_dir('pypi-client', 'PyPI'))
oauth_token_file = 'github_oauth_token'


def write_oauth_token(oauth_token: str) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    with open(config_dir / oauth_token_file, 'w') as f:
        f.write(oauth_token)


def read_oauth_token() -> str:
    try:
        with open(config_dir / oauth_token_file, 'r') as f:
            return f.readline()
    except Exception as _:
        raise Exception('Github OAuth token not found, please use `auth-github` command to obtain token')
