import os
import streamlit.components.v1 as components
from typing import Optional, Dict, Any

_COMPONENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "components", "freighter_wallet")

_freighter_wallet_component = components.declare_component(
    "freighter_wallet",
    path=_COMPONENT_DIR
)


def freighter_wallet_connect(
    unsigned_xdr: Optional[str] = None,
    action_label: Optional[str] = None,
    connected_address: Optional[str] = None,
    key: Optional[str] = "freighter_wallet_comp"
) -> Optional[Dict[str, Any]]:
    """
    Renders the Freighter Wallet Connect & Transaction Signing custom Streamlit component.

    :param unsigned_xdr: Optional unsigned Soroban transaction envelope XDR to sign.
    :param action_label: Label describing the pending transaction action.
    :param connected_address: Current connected address from session state to keep UI in sync.
    :param key: Streamlit component unique key.
    :return: Dictionary containing wallet state and signing status.
    """
    return _freighter_wallet_component(
        unsigned_xdr=unsigned_xdr,
        action_label=action_label,
        connected_address=connected_address,
        key=key,
        default=None
    )
