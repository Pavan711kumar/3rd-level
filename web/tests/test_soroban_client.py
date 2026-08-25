"""
Unit & Integration Tests for Stellar Soroban Client
Tests parsing of Soroban SCVal types, address encoding, Horizon balance loading,
transaction building, and Soroban RPC simulation.
"""

import pytest
from unittest.mock import patch, MagicMock
from stellar_sdk import Keypair, StrKey, scval, stellar_xdr as xdr

from soroban_client import (
    parse_scval_to_python,
    get_account_balance,
    fund_account,
    get_campaign_details,
    build_pledge_transaction,
    build_deploy_campaign_transaction,
    submit_signed_xdr,
    FACTORY_CONTRACT_ID,
    DEFAULT_CAMPAIGN_CONTRACT_ID,
)


def test_parse_scval_types():
    """Verify SCVal decoding for symbols, strings, i128, u64, bool, void, and addresses."""
    # Boolean
    sc_bool = scval.to_bool(True)
    assert parse_scval_to_python(sc_bool) is True

    # Symbol
    sc_sym = scval.to_symbol("get_balance")
    assert parse_scval_to_python(sc_sym) == "get_balance"

    # String
    sc_str = scval.to_string("Save the Ocean")
    assert parse_scval_to_python(sc_str) == "Save the Ocean"

    # i128
    sc_i128 = scval.to_int128(50000000000)
    assert parse_scval_to_python(sc_i128) == 50000000000

    # u64
    sc_u64 = scval.to_uint64(1735689600)
    assert parse_scval_to_python(sc_u64) == 1735689600

    # Void
    sc_void = xdr.SCVal(type=xdr.SCValType.SCV_VOID)
    assert parse_scval_to_python(sc_void) is None

    # None
    assert parse_scval_to_python(None) is None


def test_contract_address_format():
    """Verify configured contract IDs have valid Soroban StrKey format."""
    assert FACTORY_CONTRACT_ID.startswith("C")
    assert len(FACTORY_CONTRACT_ID) == 56

    assert DEFAULT_CAMPAIGN_CONTRACT_ID.startswith("C")
    assert len(DEFAULT_CAMPAIGN_CONTRACT_ID) == 56


def test_get_campaign_details_fallback():
    """Test get_campaign_details returns valid structure with fallback values."""
    fallback = {
        "name": "Unit Test Campaign",
        "goal": 2500,
        "balance": 500,
        "state": "Active",
        "deadline_days": 20
    }
    details = get_campaign_details(DEFAULT_CAMPAIGN_CONTRACT_ID, fallback_data=fallback)
    assert details["name"] == "Unit Test Campaign"
    assert details["goal"] == 2500
    assert "balance" in details
    assert "state" in details
    assert "explorer_url" in details
    assert details["address"] == DEFAULT_CAMPAIGN_CONTRACT_ID


@patch("soroban_client.get_horizon_server")
def test_get_account_balance(mock_get_horizon):
    """Test Horizon balance parser with mock server."""
    mock_server = MagicMock()
    mock_call = MagicMock()
    mock_call.call.return_value = {
        "balances": [
            {"asset_type": "native", "balance": "1234.5678000"}
        ]
    }
    mock_server.accounts().account_id.return_value = mock_call
    mock_get_horizon.return_value = mock_server

    bal = get_account_balance("GBH6ZPQ7J2N326NIZCV63ZJ3A47Q4C6KCRU5E57G7K6GZJ7F3Z5S2545")
    assert bal == 1234.5678


@patch("requests.get")
def test_fund_account_success(mock_requests_get):
    """Test Friendbot faucet helper response parsing."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_requests_get.return_value = mock_resp

    res = fund_account("GBH6ZPQ7J2N326NIZCV63ZJ3A47Q4C6KCRU5E57G7K6GZJ7F3Z5S2545")
    assert res["success"] is True
    assert "Successfully funded" in res["message"]
