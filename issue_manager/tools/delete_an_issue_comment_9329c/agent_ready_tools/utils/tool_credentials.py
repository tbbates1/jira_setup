from pathlib import Path
from typing import Any, Optional

import yaml

# Suffix config dictates which system uses which app-id suffix.
#   Created in multifile_tools.py during tool deliverables building.
SUFFIX_CONFIG_PATH = "agent_ready_tools/configs/suffix.yaml"


def published_app_id(app_id: str) -> str:
    """
    Returns the given app_id with the given suffix appended if needed.

    Arguments:
        app_id (str): Expected app_id

    Returns:
        str: App_id with the suffix added if needed. (for Saas/Catalog)
    """

    def load_suffix_config() -> Optional[dict[str, Any]]:
        """
        Attempt to find the suffix config file if it exists.

        Has to be flexible enough to work within a pants env, TRM, and a dev's environment.
        Config is added during tool deliverables building, but shouldn't fail if tool code is
        interpreted outside prior to importing.

        Returns:
            Suffix config data (dict) else None if config not found.
        """

        file_path = Path(__file__)

        # Iterate through parts to find 'agent_ready_tools'
        agent_ready_tools_parent = ""
        for i, part in enumerate(file_path.parts):
            if part == "agent_ready_tools":
                # Get the parent path (everything before agent_ready_tools)
                base_path = Path(*file_path.parts[:i])
                agent_ready_tools_parent = str(base_path) + "/"
                break

        suffix_config = Path(agent_ready_tools_parent) / SUFFIX_CONFIG_PATH

        if not suffix_config.exists():
            suffix_config.parent.mkdir(parents=True, exist_ok=True)
            suffix_data = {"suffix": "_ibm_184bdbd3"}
            yaml.safe_dump(
                suffix_data,
                suffix_config.open("w"),
                default_flow_style=False,
            )

        return yaml.load(suffix_config.open(), Loader=yaml.SafeLoader)

    suffix_data = load_suffix_config()
    suffix = "" if suffix_data is None else suffix_data["suffix"]
    return app_id + suffix
