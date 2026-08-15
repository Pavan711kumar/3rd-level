# Stellar Crowdfund - Orange Belt Submission

A Decentralized Crowdfunding platform built on Stellar using **Python and Rust only**. 
This project fulfills the Level 3 (Orange Belt) requirements for the Stellar Journey to Mastery challenge.

## 🛠️ Architecture & Tech Stack

- **Smart Contracts**: Rust (Soroban)
  - `Factory`: Deploys new campaign contracts.
  - `Campaign`: Handles goal tracking, funding, and state management (Active, Successful, Failed).
- **Frontend UI**: Python (Streamlit)
  - Mobile-responsive pure Python web app.
  - Integrates with `stellar-sdk` for simulated wallets and contract interactions.
- **CI/CD Pipeline**: GitHub Actions
  - Automatically runs Rust tests (`cargo test`) and Python tests on every push/PR.
- **Deployment**: Python script (`deploy.py`) to easily build and deploy contracts.

## 🚀 Setup & Execution

### Prerequisites
1. **Python 3.10+**
2. **Rust & Cargo** (for building smart contracts)
3. **Soroban CLI** (optional, for local testing)

### 1. Smart Contracts
To build and test the Rust Soroban contracts:

```bash
cd contracts
cargo test
cargo build --target wasm32-unknown-unknown --release
```

### 2. Frontend (Streamlit)
To run the pure Python web application:

```bash
cd web
pip install -r requirements.txt
streamlit run app.py
```
The app will open at `http://localhost:8501`.

### 3. Deployment
To deploy the contracts to the Stellar Testnet:

```bash
python deploy.py --secret <YOUR_TESTNET_SECRET>
```

## ✅ Submission Requirements Fulfilled
- [x] **Advanced smart contract development**: Factory and Campaign architecture.
- [x] **Inter-contract communication**: Factory deploying Campaign contracts.
- [x] **CI/CD pipeline setup**: GitHub Actions configured in `.github/workflows/ci.yml`.
- [x] **Smart contract deployment workflow**: Handled via `deploy.py`.
- [x] **Mobile responsive frontend development**: Built with Streamlit (fully responsive out of the box).
- [x] **Writing tests for contracts and frontend**: Rust unit tests included in `contracts/*/src/test.rs`.

## 📷 Screenshots
*(Please add screenshots of the UI, CI pipeline, and test output to the `screenshots/` folder before submitting)*
