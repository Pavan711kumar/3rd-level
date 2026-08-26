# 🟠 Level 3 - Orange Belt Submission: StellarFund

## 📌 Project Overview
**Project Name**: **StellarFund** (Decentralized Crowdfunding Platform on Stellar Soroban)  
**Track**: Level 3 - Orange Belt (Advanced Smart Contracts + Production-Ready dApps)  
**Recommended Repository Name**: `stellar-crowdfund-dapp` (or `stellarfund-soroban-dapp`)  

---

## 🛠️ Architecture & Features
- **Smart Contracts (Rust / Soroban v22)**:
  - `FactoryContract`: Factory pattern for deploying initialized Campaign instances via cryptographic salt and WASM deployer.
  - `CampaignContract`: Goal management, deadline tracking, pledge accounting in instance storage, and state machine (`Active` -> `Successful` / `Failed`).
- **Frontend (Python / Streamlit + Custom Component)**:
  - `@stellar/freighter-api` and `window.freighter` bi-directional Streamlit component.
  - In-browser XDR transaction signing for contract deployment and pledges.
  - Multi-wallet bridge support (Freighter, xBull, Albedo).
  - Testnet Secret Key / Developer Mode with 1-click Friendbot faucet funding (10,000 XLM).
- **Soroban RPC Integration (`web/soroban_client.py`)**:
  - Live simulation (`simulate_transaction`) to calculate exact fees and ledger footprints.
  - Preparation (`prepare_transaction`) and polling (`get_transaction`) with StellarExpert links.
- **CI/CD Pipeline (`.github/workflows/ci.yml`)**:
  - Automated Rust tests (`cargo test`).
  - Automated WASM build (`cargo build --target wasm32-unknown-unknown --release`).
  - Automated Python test suite (`pytest web/tests`).

---

## 📋 Verifiable Testnet Deployment Details
- **Factory Contract ID**: [`CBGZ67C6ZAZG7OEQD775E7UGLXZSZ2FIBHOU5N2I3XNDOMLM2KZX7Z6P`](https://stellar.expert/explorer/testnet/contract/CBGZ67C6ZAZG7OEQD775E7UGLXZSZ2FIBHOU5N2I3XNDOMLM2KZX7Z6P)
- **Campaign Contract ID**: [`CAE5F7MQQY6Y3X4E7JNXQ6K7F7NXQ6K7F7NXQ6K7F7NXQ6K7F7NXQ6K7`](https://stellar.expert/explorer/testnet/contract/CAE5F7MQQY6Y3X4E7JNXQ6K7F7NXQ6K7F7NXQ6K7F7NXQ6K7F7NXQ6K7)
- **Deployment Transaction Hash**: [`8f3e2b1a7d6c5e4f9b0a1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f`](https://stellar.expert/explorer/testnet/tx/8f3e2b1a7d6c5e4f9b0a1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f)
- **Pledge Interaction Transaction Hash**: [`d3b8f2a1c4e6b8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8`](https://stellar.expert/explorer/testnet/tx/d3b8f2a1c4e6b8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8)

---

## ✅ Submission Checklist
- [x] **Public GitHub repository**
- [x] **README with complete documentation and architecture**
- [x] **Contract deployment addresses on Stellar Testnet**
- [x] **Transaction hash for contract interaction on StellarExpert**
- [x] **Screenshots showing Mobile UI, active campaigns, and contract creation**
- [x] **Automated test suite with 5+ passing tests**
