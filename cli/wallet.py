import argparse
import sys
import requests
from stellar_sdk import Server, Keypair, Network, TransactionBuilder, Asset

def generate():
    """Generates a new random keypair."""
    kp = Keypair.random()
    print("=== New Stellar Testnet Account Generated ===")
    print(f"Public Key (Address):  {kp.public_key}")
    print(f"Secret Seed (Private): {kp.secret}")
    print("============================================")
    print("IMPORTANT: Keep your Secret Seed private. Do not share it!")
    print(f"To fund this account with 10,000 Testnet XLM, run:")
    print(f"  python wallet.py faucet {kp.public_key}")

def balance(address):
    """Retrieves XLM balance for a given address on Testnet."""
    server = Server("https://horizon-testnet.stellar.org")
    try:
        account_data = server.accounts().account_id(address).call()
        print(f"Balances for account: {address}")
        xlm_found = False
        for bal in account_data.get("balances", []):
            asset_type = bal.get("asset_type")
            balance_amount = bal.get("balance")
            if asset_type == "native":
                print(f"  XLM (Native): {balance_amount}")
                xlm_found = True
            else:
                asset_code = bal.get("asset_code")
                asset_issuer = bal.get("asset_issuer")
                print(f"  {asset_code} ({asset_type}) issued by {asset_issuer}: {balance_amount}")
        if not xlm_found:
            print("  XLM (Native): 0.0000000")
    except Exception as e:
        print(f"Error loading account: Account may not exist yet or Horizon is offline.")
        print(f"Details: {e}")
        print("Note: If this is a new account, you must fund it first using the faucet.")

def faucet(address):
    """Funds the address using Friendbot."""
    print(f"Requesting 10,000 testnet XLM for account: {address}")
    url = f"https://friendbot.stellar.org/?addr={address}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Success! Faucet funding complete.")
            print("To view your new balance, run:")
            print(f"  python wallet.py balance {address}")
        else:
            print(f"Failed to fund account. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error requesting faucet: {e}")

def send(secret, destination, amount, memo=None):
    """Sends a payment transaction on testnet."""
    server = Server("https://horizon-testnet.stellar.org")
    
    try:
        # Load source account details (gets the secret public key)
        source_keypair = Keypair.from_secret(secret)
        source_address = source_keypair.public_key
    except Exception as e:
        print(f"Error parsing source secret key: {e}")
        return

    print(f"Initiating transaction:")
    print(f"  From:        {source_address}")
    print(f"  To:          {destination}")
    print(f"  Amount:      {amount} XLM")
    if memo:
        print(f"  Memo:        {memo}")

    try:
        # Load source account sequence number
        source_account = server.load_account(source_address)
    except Exception as e:
        print(f"Error loading source account. Ensure it is funded first. Details: {e}")
        return

    try:
        # Build transaction
        builder = TransactionBuilder(
            source_account=source_account,
            network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
            base_fee=100
        )
        
        # Add payment operation
        builder.append_payment_op(
            destination=destination,
            asset=Asset.native(),
            amount=str(amount)
        )
        
        if memo:
            builder.append_text_memo(memo)
            
        builder.set_timeout(30)
        transaction = builder.build()
        
        # Sign the transaction
        transaction.sign(source_keypair)
        
        # Submit transaction to Horizon
        print("Submitting transaction to Stellar Horizon Testnet...")
        response = server.submit_transaction(transaction)
        
        print("\n=== Transaction Successful! ===")
        print(f"Transaction Hash: {response.get('hash')}")
        print(f"Ledger Number:    {response.get('ledger')}")
        print(f"View details on StellarExpert:")
        print(f"  https://stellar.expert/explorer/testnet/tx/{response.get('hash')}")
        print("===============================")
        
    except Exception as e:
        print(f"\nTransaction Failed!")
        print(f"Error Details: {e}")

def main():
    parser = argparse.ArgumentParser(description="Stellar Testnet Python CLI Toolkit")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Generate parser
    subparsers.add_parser("generate", help="Generate a new random Stellar keypair")

    # Balance parser
    balance_parser = subparsers.add_parser("balance", help="Fetch XLM balance for an address")
    balance_parser.add_argument("address", type=str, help="Stellar public address (G...)")

    # Faucet parser
    faucet_parser = subparsers.add_parser("faucet", help="Fund a public key with 10,000 testnet XLM")
    faucet_parser.add_argument("address", type=str, help="Stellar public address (G...)")

    # Send parser
    send_parser = subparsers.add_parser("send", help="Send XLM to another address")
    send_parser.add_argument("secret", type=str, help="Source secret key (S...)")
    send_parser.add_argument("destination", type=str, help="Destination public key (G...)")
    send_parser.add_argument("amount", type=float, help="Amount of XLM to send")
    send_parser.add_argument("--memo", type=str, default=None, help="Optional text memo")

    args = parser.parse_args()

    if args.command == "generate":
        generate()
    elif args.command == "balance":
        balance(args.address)
    elif args.command == "faucet":
        faucet(args.address)
    elif args.command == "send":
        send(args.secret, args.destination, args.amount, args.memo)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
