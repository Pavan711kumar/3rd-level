import streamlit as st
from stellar_sdk import Keypair
import time

st.set_page_config(page_title="Stellar Crowdfund", layout="centered", page_icon="🍊")

# --- Custom CSS for some minor styling ---
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 1.5rem; }
    .stProgress .st-bo { background-color: #ff4b4b; }
</style>
""", unsafe_allow_html=True)

st.title("🍊 Stellar Crowdfunding")
st.write("A decentralized crowdfunding platform built on Stellar Soroban.")

# --- Sidebar: Simulated Wallet ---
st.sidebar.header("Wallet")
wallet_type = st.sidebar.radio("Connection", ["Simulated (Generate New)", "Import Secret Seed"])

if "keypair" not in st.session_state:
    st.session_state.keypair = None

if wallet_type == "Simulated (Generate New)":
    if st.sidebar.button("Generate New Keypair"):
        kp = Keypair.random()
        st.session_state.keypair = kp
        st.sidebar.success("Generated!")
elif wallet_type == "Import Secret Seed":
    secret = st.sidebar.text_input("Secret Seed", type="password")
    if st.sidebar.button("Import") and secret:
        try:
            kp = Keypair.from_secret(secret)
            st.session_state.keypair = kp
            st.sidebar.success("Imported!")
        except Exception as e:
            st.sidebar.error(f"Invalid secret: {e}")

if st.session_state.keypair:
    st.sidebar.write(f"**Public Key:** `{st.session_state.keypair.public_key[:8]}...{st.session_state.keypair.public_key[-4:]}`")
else:
    st.sidebar.warning("Connect a wallet to pledge or create campaigns.")

# --- Main App: View Campaigns ---
st.header("Active Campaigns")

# Mock data - in a real dApp, we would fetch this via stellar-sdk querying the Factory Contract
if "campaigns" not in st.session_state:
    st.session_state.campaigns = [
        {"name": "Save the Ocean", "goal": 5000, "balance": 1200, "address": "CABC1234567890ABCDEF"},
        {"name": "Open Source Initiative", "goal": 10000, "balance": 8500, "address": "CDEF1234567890ABCDEF"},
    ]

for idx, camp in enumerate(st.session_state.campaigns):
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(camp["name"])
            st.write(f"**Contract:** `{camp['address'][:8]}...`")
            progress = min(camp["balance"] / camp["goal"], 1.0)
            st.progress(progress, text=f"Raised: {camp['balance']} / {camp['goal']} XLM")
        with col2:
            st.write("")
            st.write("")
            if st.button("Pledge 100 XLM", key=camp["address"]):
                if not st.session_state.keypair:
                    st.error("Please connect a wallet first.")
                else:
                    with st.spinner("Submitting Soroban transaction..."):
                        # Mocking transaction delay
                        time.sleep(2)
                        st.session_state.campaigns[idx]["balance"] += 100
                        st.success(f"Pledged 100 XLM! (Tx: `d3b...8f2`)")
                        time.sleep(1)
                        st.rerun()

# --- Main App: Create Campaign ---
st.header("Create a Campaign")
with st.form("create_campaign"):
    c_name = st.text_input("Campaign Name")
    c_goal = st.number_input("Goal Amount (XLM)", min_value=1, value=1000)
    c_days = st.number_input("Duration (Days)", min_value=1, value=30)
    
    submitted = st.form_submit_button("Deploy Contract")
    if submitted:
        if not st.session_state.keypair:
            st.error("Please connect a wallet first.")
        else:
            with st.spinner("Deploying Campaign Contract via Factory..."):
                time.sleep(3)
                new_camp = {
                    "name": c_name,
                    "goal": c_goal,
                    "balance": 0,
                    "address": f"CNEW{int(time.time())}ABCDEF"
                }
                st.session_state.campaigns.append(new_camp)
                st.success(f"Campaign '{c_name}' created successfully!")
                time.sleep(1)
                st.rerun()
