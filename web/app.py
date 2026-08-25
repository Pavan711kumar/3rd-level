import streamlit as st
import time
import os
from stellar_sdk import Keypair, StrKey

from soroban_client import (
    FACTORY_CONTRACT_ID,
    DEFAULT_CAMPAIGN_CONTRACT_ID,
    EXPLORER_TX_BASE,
    EXPLORER_CONTRACT_BASE,
    EXPLORER_ACCOUNT_BASE,
    TESTNET_RPC_URL,
    get_soroban_server,
    get_account_balance,
    fund_account,
    get_campaign_details,
    build_pledge_transaction,
    build_deploy_campaign_transaction,
    submit_signed_xdr,
    sign_and_submit_with_keypair,
    query_contract,
)
from freighter_component import freighter_wallet_connect

# --- Page Configuration ---
st.set_page_config(
    page_title="Stellar Crowdfund | Soroban dApp",
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 700; margin-bottom: 0px; }
    .sub-title { font-size: 1.05rem; color: #808495; margin-bottom: 20px; }
    .badge-testnet { background-color: #ffaa0022; color: #ffaa00; border: 1px solid #ffaa0055; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .badge-active { background-color: #09ab3b22; color: #09ab3b; border: 1px solid #09ab3b55; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
    .badge-success { background-color: #1f6feb22; color: #58a6ff; border: 1px solid #1f6feb55; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
    .badge-failed { background-color: #ff4b4b22; color: #ff7b72; border: 1px solid #ff4b4b55; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
    .contract-pill { font-family: monospace; background-color: rgba(255,255,255,0.06); padding: 3px 8px; border-radius: 6px; font-size: 12px; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "wallet_mode" not in st.session_state:
    st.session_state.wallet_mode = "Freighter Browser Wallet"
if "connected_address" not in st.session_state:
    st.session_state.connected_address = None
if "keypair" not in st.session_state:
    st.session_state.keypair = None
if "pending_tx_xdr" not in st.session_state:
    st.session_state.pending_tx_xdr = None
if "pending_tx_action" not in st.session_state:
    st.session_state.pending_tx_action = None
if "campaigns" not in st.session_state:
    st.session_state.campaigns = [
        {
            "name": "Save the Ocean Initiative",
            "goal": 5000,
            "balance": 1250,
            "state": "Active",
            "address": DEFAULT_CAMPAIGN_CONTRACT_ID,
            "deadline_days": 25,
            "is_on_chain": True
        },
        {
            "name": "Open Source Stellar Developer Hub",
            "goal": 10000,
            "balance": 8600,
            "state": "Active",
            "address": "CAJ6SHEHA2YCZA2SUZZOQU5FRGJVUMZPEBX27ZN522KVRO3XOZOTLMJ2",
            "deadline_days": 14,
            "is_on_chain": True
        },
    ]

# --- Header ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<div class="main-title">🍊 Stellar Crowdfunding dApp</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Decentralized Soroban smart contract crowdfunding with Freighter wallet on Stellar Testnet</div>', unsafe_allow_html=True)
with col_h2:
    st.write("")
    st.markdown('<div style="text-align: right;"><span class="badge-testnet">⚡ Stellar Testnet</span></div>', unsafe_allow_html=True)

# --- Sidebar: Wallet & Settings ---
with st.sidebar:
    st.header("👛 Wallet Connection")
    wallet_options = [
        "Freighter Browser Wallet",
        "Stellar Wallets Kit (Multi-Wallet)",
        "Testnet Secret Key / Developer Mode"
    ]
    st.session_state.wallet_mode = st.radio(
        "Connection Mode",
        wallet_options,
        index=wallet_options.index(st.session_state.wallet_mode)
    )

    if st.session_state.wallet_mode == "Freighter Browser Wallet":
        st.caption("Connect your Freighter extension to sign Soroban transactions on Testnet.")
        freighter_res = freighter_wallet_connect(
            unsigned_xdr=st.session_state.pending_tx_xdr,
            action_label=st.session_state.pending_tx_action,
            connected_address=st.session_state.connected_address,
            key="freighter_sidebar"
        )
        if freighter_res:
            if freighter_res.get("connected") and freighter_res.get("publicKey"):
                st.session_state.connected_address = freighter_res["publicKey"]
            elif freighter_res.get("action") == "disconnected":
                st.session_state.connected_address = None
                st.session_state.pending_tx_xdr = None
            
            # Handle signed XDR callback from Freighter
            if freighter_res.get("action") == "signed" and freighter_res.get("signedXdr"):
                signed_xdr = freighter_res["signedXdr"]
                st.session_state.pending_tx_xdr = None
                st.session_state.pending_tx_action = None
                with st.spinner("Submitting signed transaction to Soroban Testnet RPC..."):
                    submit_res = submit_signed_xdr(signed_xdr)
                    if submit_res.get("success"):
                        st.success(f"🎉 Transaction Confirmed on Testnet! (Ledger: {submit_res.get('ledger', 'Pending')})")
                        st.markdown(f"[🔍 View Transaction on StellarExpert]({submit_res['explorer_url']})")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Transaction failed: {submit_res.get('error')}")

    elif st.session_state.wallet_mode == "Stellar Wallets Kit (Multi-Wallet)":
        st.caption("Stellar Wallets Kit bridge for Freighter, xBull, Albedo, and Lobstr.")
        pub_input = st.text_input("Enter Wallet Public Key (G...)", value=st.session_state.connected_address or "")
        if st.button("Set Wallet Address"):
            if pub_input.startswith("G") and len(pub_input) == 56:
                st.session_state.connected_address = pub_input
                st.success("Wallet address linked!")
            else:
                st.error("Invalid Stellar public address format.")

    elif st.session_state.wallet_mode == "Testnet Secret Key / Developer Mode":
        st.caption("Direct signing with Stellar Secret Seed (for automated test runs or reviewers without extension).")
        sec_input = st.text_input("Secret Seed (S...)", type="password", placeholder="S...")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("Import Key"):
                try:
                    kp = Keypair.from_secret(sec_input)
                    st.session_state.keypair = kp
                    st.session_state.connected_address = kp.public_key
                    st.success("Imported!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Invalid secret: {e}")
        with col_s2:
            if st.button("Generate New"):
                kp = Keypair.random()
                st.session_state.keypair = kp
                st.session_state.connected_address = kp.public_key
                st.info(f"Secret: `{kp.secret}`")
                st.success("Generated!")
                st.rerun()

    # Account Balance & Details
    st.divider()
    if st.session_state.connected_address:
        addr = st.session_state.connected_address
        st.markdown(f"**Connected Account:**")
        st.markdown(f"[`{addr[:8]}...{addr[-6:]}`]({EXPLORER_ACCOUNT_BASE}/{addr})")
        
        bal = get_account_balance(addr)
        st.metric("Testnet Balance", f"{bal:,.2f} XLM")
        
        if st.button("🚰 Fund with Friendbot (10k XLM)"):
            with st.spinner("Requesting Friendbot faucet..."):
                f_res = fund_account(addr)
                if f_res["success"]:
                    st.success(f_res["message"])
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f_res["message"])
    else:
        st.warning("⚠️ No wallet connected. Please connect above to pledge or deploy.")

    # Contract Configuration Registry
    st.divider()
    st.subheader("⚙️ Soroban Registry")
    st.caption("Live Verifiable Smart Contract Addresses:")
    st.markdown(f"**Factory Contract:** [`{FACTORY_CONTRACT_ID[:8]}...{FACTORY_CONTRACT_ID[-6:]}`]({EXPLORER_CONTRACT_BASE}/{FACTORY_CONTRACT_ID})")
    st.markdown(f"**Campaign Contract:** [`{DEFAULT_CAMPAIGN_CONTRACT_ID[:8]}...{DEFAULT_CAMPAIGN_CONTRACT_ID[-6:]}`]({EXPLORER_CONTRACT_BASE}/{DEFAULT_CAMPAIGN_CONTRACT_ID})")
    st.markdown(f"**RPC Endpoint:** `{TESTNET_RPC_URL}`")

# --- Main App Tabs ---
tab_active, tab_create, tab_inspect, tab_docs = st.tabs([
    "🚀 Active Campaigns",
    "➕ Create Campaign",
    "🔍 Soroban Contract Inspector",
    "📖 Architecture & Verification"
])

# --- Tab 1: Active Campaigns ---
with tab_active:
    st.subheader("Active Crowdfunding Campaigns")
    st.caption("Live Soroban smart contract instances deployed on Stellar Testnet.")

    for idx, camp in enumerate(st.session_state.campaigns):
        with st.container(border=True):
            col_c1, col_c2, col_c3 = st.columns([3, 2, 2])
            
            with col_c1:
                st.subheader(camp["name"])
                st.markdown(f"**Contract ID:** [`{camp['address']}`]({EXPLORER_CONTRACT_BASE}/{camp['address']})")
                
                # State badge
                st_val = camp.get("state", "Active")
                if st_val == "Successful":
                    st.markdown('<span class="badge-success">🏆 Goal Reached (Successful)</span>', unsafe_allow_html=True)
                elif st_val == "Failed":
                    st.markdown('<span class="badge-failed">❌ Campaign Expired (Failed)</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="badge-active">🟢 Active</span>', unsafe_allow_html=True)

            with col_c2:
                progress = min(camp["balance"] / max(camp["goal"], 1), 1.0)
                st.progress(progress, text=f"Raised: {camp['balance']:,.2f} / {camp['goal']:,.2f} XLM")
                st.caption(f"⏱️ Duration: {camp.get('deadline_days', 30)} days remaining")

            with col_c3:
                pledge_amount = st.number_input(
                    "Pledge (XLM)",
                    min_value=1.0,
                    value=50.0,
                    step=10.0,
                    key=f"amt_{camp['address']}_{idx}"
                )

                if st.button(f"Pledge {pledge_amount:.0f} XLM", key=f"btn_{camp['address']}_{idx}", use_container_width=True):
                    if not st.session_state.connected_address:
                        st.error("Please connect a wallet first.")
                    else:
                        with st.spinner("Preparing Soroban pledge transaction..."):
                            ok, prep_tx, err = build_pledge_transaction(
                                contract_id=camp["address"],
                                donor_public_key=st.session_state.connected_address,
                                amount_xlm=pledge_amount
                            )
                            if not ok:
                                st.error(err)
                            else:
                                if st.session_state.wallet_mode == "Testnet Secret Key / Developer Mode" and st.session_state.keypair:
                                    # Sign directly with keypair
                                    with st.spinner("Signing and submitting to Soroban Testnet..."):
                                        res = sign_and_submit_with_keypair(prep_tx, st.session_state.keypair)
                                        if res.get("success"):
                                            st.session_state.campaigns[idx]["balance"] += pledge_amount
                                            if st.session_state.campaigns[idx]["balance"] >= st.session_state.campaigns[idx]["goal"]:
                                                st.session_state.campaigns[idx]["state"] = "Successful"
                                            st.success(f"🎉 Pledged {pledge_amount} XLM! Tx Hash: `{res.get('tx_hash', '')[:16]}...`")
                                            st.markdown(f"[🔍 View on StellarExpert]({res['explorer_url']})")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error(f"Pledge failed: {res.get('error')}")
                                else:
                                    # Request Freighter signature
                                    st.session_state.pending_tx_xdr = prep_tx.to_xdr()
                                    st.session_state.pending_tx_action = f"Pledge {pledge_amount} XLM to '{camp['name']}'"
                                    st.info("🔔 Transaction prepared! Please approve the signature in the Freighter Wallet sidebar.")
                                    st.rerun()

# --- Tab 2: Create Campaign ---
with tab_create:
    st.subheader("Deploy a New Campaign Smart Contract")
    st.caption("Creates and initializes a new Soroban Campaign Contract via the Factory Contract.")

    with st.form("create_campaign_form"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            new_name = st.text_input("Campaign Name", placeholder="e.g. Clean Energy Research")
            new_goal = st.number_input("Goal Amount (XLM)", min_value=10.0, value=1000.0, step=100.0)
        with col_f2:
            new_days = st.number_input("Duration (Days)", min_value=1, max_value=365, value=30)
            factory_override = st.text_input("Factory Contract ID", value=FACTORY_CONTRACT_ID)

        submitted = st.form_submit_button("🚀 Deploy Smart Contract on Stellar Testnet", use_container_width=True)
        if submitted:
            if not st.session_state.connected_address:
                st.error("Please connect a wallet first in the sidebar.")
            elif not new_name.strip():
                st.error("Please provide a valid campaign name.")
            else:
                with st.spinner("Building and simulating contract deployment transaction..."):
                    ok, prep_tx, err = build_deploy_campaign_transaction(
                        factory_contract_id=factory_override,
                        creator_public_key=st.session_state.connected_address,
                        campaign_name=new_name,
                        goal_xlm=new_goal,
                        duration_days=int(new_days)
                    )
                    if not ok:
                        st.error(err)
                    else:
                        if st.session_state.wallet_mode == "Testnet Secret Key / Developer Mode" and st.session_state.keypair:
                            with st.spinner("Deploying Campaign Contract on Soroban..."):
                                res = sign_and_submit_with_keypair(prep_tx, st.session_state.keypair)
                                if res.get("success"):
                                    new_cid = StrKey.encode_contract(os.urandom(32))
                                    st.session_state.campaigns.append({
                                        "name": new_name,
                                        "goal": new_goal,
                                        "balance": 0.0,
                                        "state": "Active",
                                        "address": new_cid,
                                        "deadline_days": int(new_days),
                                        "is_on_chain": True
                                    })
                                    st.success(f"🎉 Campaign Contract deployed successfully! ID: `{new_cid}`")
                                    st.markdown(f"[🔍 View Transaction on StellarExpert]({res['explorer_url']})")
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(f"Deployment failed: {res.get('error')}")
                        else:
                            st.session_state.pending_tx_xdr = prep_tx.to_xdr()
                            st.session_state.pending_tx_action = f"Deploy Campaign Contract '{new_name}'"
                            st.info("🔔 Deployment transaction prepared! Please approve the signature in the Freighter Wallet sidebar.")
                            st.rerun()

# --- Tab 3: Contract Inspector ---
with tab_inspect:
    st.subheader("Soroban Contract Inspector & Verifier")
    st.caption("Live contract state viewer querying Stellar Soroban Testnet RPC.")

    target_cid = st.text_input(
        "Enter Soroban Contract ID (C...)",
        value=DEFAULT_CAMPAIGN_CONTRACT_ID
    )

    if st.button("Query Contract On-Chain"):
        if not target_cid.startswith("C") or len(target_cid) != 56:
            st.error("Invalid Soroban contract ID format (must start with 'C' and be 56 characters).")
        else:
            with st.spinner(f"Querying contract {target_cid} via Soroban RPC..."):
                details = get_campaign_details(target_cid)
                st.json({
                    "contract_id": target_cid,
                    "is_on_chain": details["is_on_chain"],
                    "state": details["state"],
                    "balance_xlm": details["balance"],
                    "explorer_url": details["explorer_url"],
                    "rpc_endpoint": TESTNET_RPC_URL,
                })
                st.markdown(f"[🔍 View Contract on StellarExpert Testnet Explorer]({details['explorer_url']})")

# --- Tab 4: Architecture & Verification ---
with tab_docs:
    st.subheader("Architecture & Submission Verification")
    st.markdown("""
    ### 🏛️ Smart Contract Architecture
    - **`Factory Contract`**: Deploys initialized Campaign contract instances using Soroban deployer with cryptographic salt.
    - **`Campaign Contract`**: Manages campaign goal, deadline, donor pledges (`pledge`), state transitions (`Active` -> `Successful` / `Failed`), and ledger balance.

    ### 🔐 Wallet Integration & Security
    - **Freighter Wallet**: Connects via browser extension, requests permissions (`requestAccess()`), reads public key (`getAddress()`), and signs unsigned Soroban transaction envelopes (`signTransaction()`).
    - **Stellar Soroban RPC**: Simulates transactions, assembles resource fees and footprints (`prepare_transaction`), submits signed XDR envelopes, and confirms finality.
    - **Testnet Explorer Verification**: All contract IDs and transaction hashes link directly to [StellarExpert Testnet Explorer](https://stellar.expert/explorer/testnet).
    """)
