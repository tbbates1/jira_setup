"""
NOTE: The structure and contents of this file are tied to the import script for importing tools.
Please ensure tools can properly be imported and authenticated into the SDK server after making changes.
"""

from enum import StrEnum
import json
from pathlib import Path
from typing import Dict, List, Optional

from ibm_watsonx_orchestrate.agent_builder.connections.types import (
    ConnectionType,
    ExpectedCredentials,
    KeyValueConnectionCredentials,
)
from ibm_watsonx_orchestrate.utils.exceptions import BadRequest

from agent_ready_tools.utils.env import in_pants_env
from agent_ready_tools.utils.systems import Systems


class CredentialKeys(StrEnum):
    """Types of credential keys for different systems."""

    API_KEY = "api_key"
    AUTHORITY = "authority"
    BASE_URL = "base_url"
    BEARER_TOKEN = "bearer_token"
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"
    CLIENT_CERT = "client_cert"
    CLIENT_KEY = "client_key"
    PASSWORD = "password"
    REALM = "realm"
    REFRESH_TOKEN = "refresh_token"
    SUBJECT_ID = "subject_id"
    SUBJECT_TYPE = "subject_type"
    TENANT_ID = "tenant_id"
    TENANT_NAME = "tenant_name"
    TOKEN_URL = "token_url"
    USER_ID = "user_id"
    USERNAME = "username"
    BUYER_ANID = "buyer_anid"
    ACCESS_KEY = "access_key"
    SECRET_KEY = "secret_key"
    REGION = "region"
    REQUESTER_PASSWORD = "requester_password"
    DELEGATE_MODE = "delegate_mode"
    SCOPE = "scope"
    INSTANCE_ID = "instance_id"
    MODEL_NAME = "model_name"
    PASSWORD_ADAPTER = "password_adapter"
    DATABASE = "database"
    PORT = "port"


def _merge_base_and_subcategory(system_creds: Dict, sub_category: Optional[str] = None) -> Dict:
    """
    Returns the base credential values and any values for the specified sub_category.

    Args:
        system_creds: The complete set of credentials for a given system.
        sub_category: The sub-category of creds desired.

    Returns:
        Dict of merged creds.
    """
    if sub_category:
        return {k: v for k, v in system_creds.items() if isinstance(v, str)} | system_creds[
            sub_category
        ]
    else:
        return system_creds


def _merge_key_value_creds(kv_creds: KeyValueConnectionCredentials, merged_creds: Dict) -> Dict:
    """
    Merges existing creds (in merged_creds) with key_value creds retrieved from WxO.

    Args:
        kv_creds: Key-Value creds retrieved to merge into merged_creds.
        merged_creds: Existing dict of creds for system.

    Returns:
        Merged creds dict.
    """
    for key, new_value in kv_creds.items():
        existing_value = merged_creds.get(key)
        # orchestrate sometimes returns 'None' instead of actual None
        if not new_value or new_value == "None":
            continue
        if not existing_value or existing_value == "None":
            merged_creds[key] = new_value
            continue
        if existing_value != new_value:
            raise ValueError(
                f"System has two same keys '{key}' in credentials with different values: '{new_value}' and '{existing_value}'"
            )
        merged_creds[key] = new_value
    return merged_creds


def get_tool_credentials(
    system: Optional[Systems] = None,
    sub_category: Optional[str] = None,
    expected_credentials: Optional[List[ExpectedCredentials]] = None,
) -> Dict:
    """
    Gets tools credentials from SDK server or credentials.json. Expects either system + sub_category
    or expected_credentials as input params.

    Args:
        system: The system for which to return creds.
        sub_category: A specific sub-category of creds for the given system.
        expected_credentials: Pre-defined set of expected credentials (connections) to query from WxO.

    Returns:
        Dict of creds.
    """
    if not expected_credentials:
        assert (
            system
        ), f"Either expected_credentials or system param is required to get tool credentials."

        if system in [Systems.WORKDAY, Systems.ARIBA, Systems.DNB]:
            assert (
                sub_category
            ), f"System {system} must specify a sub-category to obtain credentials."

        # local integration test, return from credentials.json
        # TODO: investigate if still needed and deprecate if not:
        # https://github.ibm.com/WatsonOrchestrate/wxo-domains/issues/9403
        if in_pants_env():
            creds_path = Path(__file__).parent / "credentials.json"
            with open(creds_path) as creds:
                system_creds: Dict = json.load(creds).get(system, {})
                return _merge_base_and_subcategory(system_creds, sub_category)

    assert expected_credentials, f"Missing expected_credentials. system = '{system}'"

    if expected_credentials:
        # Import connections here to avoid circular import issues introduced in ADK v2.3.0
        from ibm_watsonx_orchestrate.run import (  # pylint: disable=import-outside-toplevel
            connections,
        )

        merged_conn_creds: Dict = {}
        for expected_conn in expected_credentials:
            possible_conn_types = [expected_conn.type]
            if isinstance(expected_conn.type, List):
                possible_conn_types = expected_conn.type

            for connection_type in possible_conn_types:
                try:
                    if connection_type == ConnectionType.BASIC_AUTH:
                        conn = connections.basic_auth(expected_conn.app_id)
                        merged_conn_creds[CredentialKeys.USERNAME] = conn.username
                        merged_conn_creds[CredentialKeys.PASSWORD] = conn.password
                    elif connection_type == ConnectionType.BEARER_TOKEN:
                        conn = connections.bearer_token(expected_conn.app_id)
                        merged_conn_creds[CredentialKeys.BEARER_TOKEN] = conn.token
                    elif connection_type == ConnectionType.API_KEY_AUTH:
                        conn = connections.api_key_auth(expected_conn.app_id)
                        merged_conn_creds[CredentialKeys.API_KEY] = conn.api_key
                    elif connection_type == ConnectionType.OAUTH2_AUTH_CODE:
                        conn = connections.oauth2_auth_code(expected_conn.app_id)
                        merged_conn_creds[CredentialKeys.BEARER_TOKEN] = conn.access_token
                    elif connection_type == ConnectionType.OAUTH2_CLIENT_CREDS:
                        conn = connections.oauth2_client_creds(expected_conn.app_id)
                        merged_conn_creds[CredentialKeys.BEARER_TOKEN] = conn.access_token
                    elif connection_type == ConnectionType.OAUTH_ON_BEHALF_OF_FLOW:
                        conn = connections.oauth2_on_behalf_of(expected_conn.app_id)
                        merged_conn_creds[CredentialKeys.BEARER_TOKEN] = conn.access_token
                    elif connection_type == ConnectionType.OAUTH2_PASSWORD:
                        conn = connections.oauth2_password(expected_conn.app_id)
                        merged_conn_creds[CredentialKeys.BEARER_TOKEN] = conn.access_token
                    elif connection_type == ConnectionType.OAUTH2_TOKEN_EXCHANGE:
                        conn = connections.oauth2_token_exchange(expected_conn.app_id)
                        merged_conn_creds[CredentialKeys.BEARER_TOKEN] = conn.access_token
                    elif connection_type == ConnectionType.KEY_VALUE:
                        conn = connections.key_value(expected_conn.app_id)
                        merged_conn_creds = _merge_key_value_creds(merged_conn_creds, conn)
                    else:
                        raise ValueError(
                            f"ConnectionType {connection_type} for app-id {expected_conn.app_id} is not supported."
                        )
                    # Successfully retrieved credentials, break out of the loop
                    break
                except (
                    BadRequest
                ):  # not the configured conn type, try the other possible ones for this app-id
                    continue

            # ensure we got some creds
            if len(merged_conn_creds) < 1:
                raise ValueError(
                    f"No Creds retrieved for expected connections with app-ids: {[c.app_id for c in expected_credentials]}"
                )

            # backward compatibility for key_value connections containing 'base_url' created before the 'base_url' key
            # was added to all other conn types
            _none_conn_values = [None, "None", ""]

            if connection_type != ConnectionType.KEY_VALUE and conn.url not in _none_conn_values:
                # give 'base_url' in key_value conn precedence for backward compatibility in SaaS
                if merged_conn_creds.get(CredentialKeys.BASE_URL) in _none_conn_values:
                    merged_conn_creds[CredentialKeys.BASE_URL] = conn.url

        return merged_conn_creds
    else:
        # see 'create_flattened_module()' in flat_tools.py
        # TODO: remove once all APIs have 'connections' in SDK server
        all_creds: Dict = {"TODO": {}}
        system_creds = all_creds.get(system, {})
        return _merge_base_and_subcategory(system_creds, sub_category)
