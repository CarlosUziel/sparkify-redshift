from configparser import ConfigParser
from pathlib import Path


def process_config(config_path: Path) -> ConfigParser:
    """Process a single configuration file."""
    assert config_path.exists(), (
        f"User configuration file {config_path} does not exist, "
        "please create it following the README.md file of this project."
    )

    with config_path.open("r") as fp:
        config = ConfigParser()
        config.read_file(fp)

    return config
