import React, { useState, useEffect } from 'react';
import { 
  isConnected as isFreighterInstalled, 
  getAddress, 
  signTransaction 
} from '@stellar/freighter-api';
import { 
  Horizon, 
  TransactionBuilder, 
  Operation, 
  Asset, 
  Networks, 
  Transaction,
  Memo,
  Keypair
} from '@stellar/stellar-sdk';
import { 
  Wallet, 
  Send, 
  RefreshCw, 
  Coins, 
  History, 
  Moon, 
  Sun, 
  CheckCircle2, 
  XCircle, 
  Copy, 
  Check, 
  ArrowRight,
  Info,
  ExternalLink,
  Cpu
} from 'lucide-react';

const BACKEND_URL = 'http://localhost:8080';
const HORIZON_URL = 'https://horizon-testnet.stellar.org';
const server = new Horizon.Server(HORIZON_URL);

interface PaymentTx {
  id: string;
  transaction_hash: string;
  created_at: string;
  from: string;
  to: string;
  amount: string;
  asset_type: string;
}

function App() {
  // State variables
  const [address, setAddress] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [balance, setBalance] = useState<string | null>(null);
  const [xlmUsd, setXlmUsd] = useState<number>(0.102); // Default fallback price
  const [transactions, setTransactions] = useState<PaymentTx[]>([]);
  const [isDarkTheme, setIsDarkTheme] = useState<boolean>(true);
  
  // Faucet/Mock Wallet states
  const [isMockMode, setIsMockMode] = useState<boolean>(false);
  const [mockSecret, setMockSecret] = useState<string | null>(null);

  // Loading states
  const [loadingBalance, setLoadingBalance] = useState<boolean>(false);
  const [loadingFaucet, setLoadingFaucet] = useState<boolean>(false);
  const [loadingTx, setLoadingTx] = useState<boolean>(false);
  const [isCopied, setIsCopied] = useState<boolean>(false);

  // Form states
  const [recipient, setRecipient] = useState<string>('');
  const [amount, setAmount] = useState<string>('');
  const [memo, setMemo] = useState<string>('');
  const [recipientError, setRecipientError] = useState<string>('');
  const [amountError, setAmountError] = useState<string>('');

  // Transaction submission flow states
  const [txStatus, setTxStatus] = useState<'idle' | 'signing' | 'submitting' | 'success' | 'error'>('idle');
  const [txHash, setTxHash] = useState<string | null>(null);
  const [txError, setTxError] = useState<string | null>(null);

  // Set initial theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDarkTheme ? 'dark' : 'light');
  }, [isDarkTheme]);

  // Load initial settings and price feed
  useEffect(() => {
    fetchXlmPrice();
  }, []);

  // Fetch data on connection
  useEffect(() => {
    if (address) {
      fetchBalance(address);
      fetchTransactions(address);
    } else {
      setBalance(null);
      setTransactions([]);
    }
  }, [address]);

  // Check if wallet is already approved
  useEffect(() => {
    const checkWallet = async () => {
      try {
        const res = await isFreighterInstalled();
        if (res && res.isConnected && !isMockMode) {
          const result = await getAddress();
          if (result && result.address) {
            setAddress(result.address);
            setIsConnected(true);
          }
        }
      } catch (e) {
        console.log('Freighter auto-connect skipped or rejected:', e);
      }
    };
    checkWallet();
  }, [isMockMode]);

  // Fetch XLM price from Rust Backend (falls back silently)
  const fetchXlmPrice = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/price`);
      if (response.ok) {
        const data = await response.json();
        setXlmUsd(data.xlm_usd);
      }
    } catch (e) {
      console.log('Rust backend price API unavailable, using fallback price feed.', e);
    }
  };

  // Fetch Balance from Horizon Testnet
  const fetchBalance = async (accAddress: string) => {
    setLoadingBalance(true);
    try {
      const account = await server.loadAccount(accAddress);
      const nativeBalance = account.balances.find((b: any) => b.asset_type === 'native');
      if (nativeBalance) {
        // Format to 4 decimal places for clean UI representation
        const formatted = parseFloat(nativeBalance.balance).toFixed(4);
        setBalance(formatted);
      } else {
        setBalance('0.0000');
      }
    } catch (e) {
      console.error('Error loading account balance:', e);
      // If account does not exist yet (unfunded)
      setBalance('0.0000');
    } finally {
      setLoadingBalance(false);
    }
  };

  // Fetch Recent Transactions via Rust Backend (falls back directly to Horizon)
  const fetchTransactions = async (accAddress: string) => {
    setLoadingTx(true);
    try {
      // 1. Try fetching via Rust Backend
      const response = await fetch(`${BACKEND_URL}/api/transactions/${accAddress}`);
      if (response.ok) {
        const data = await response.json();
        setTransactions(data.payments);
      } else {
        throw new Error('Backend transactions endpoint failed');
      }
    } catch (e) {
      console.log('Rust backend transactions API unavailable, querying Horizon directly.', e);
      // 2. Direct Horizon Fallback
      try {
        const records = await server.payments()
          .forAccount(accAddress)
          .order('desc')
          .limit(10)
          .call();
        
        // Map Horizon records to our interface
        const mapped: PaymentTx[] = records.records.map((r: any) => ({
          id: r.id,
          transaction_hash: r.transaction_hash,
          created_at: r.created_at,
          from: r.from,
          to: r.to,
          amount: r.amount || '0',
          asset_type: r.asset_type
        }));
        setTransactions(mapped);
      } catch (err) {
        console.error('Horizon transaction query failed:', err);
      }
    } finally {
      setLoadingTx(false);
    }
  };

  // Connect Freighter Wallet
  const handleConnect = async () => {
    try {
      const res = await isFreighterInstalled();
      if (!res || !res.isConnected) {
        alert('Freighter Wallet extension is not installed or enabled! Please install it from freighter.app to continue, or click "Start Simulated Mode" below to test without it.');
        return;
      }
      
      const result = await getAddress();
      if (result.error) {
        throw new Error(result.error.message || result.error);
      }
      if (result.address) {
        setIsMockMode(false);
        setMockSecret(null);
        setAddress(result.address);
        setIsConnected(true);
      }
    } catch (e: any) {
      console.error('Wallet connection rejected:', e);
      alert(`Wallet connection failed: ${e.message || e}`);
    }
  };

  // Start Simulated Mode
  const handleStartSimulation = () => {
    const kp = Keypair.random();
    setIsMockMode(true);
    setMockSecret(kp.secret());
    setAddress(kp.publicKey());
    setIsConnected(true);
    // Let the user know
    alert('Simulated Mode Started! We have generated a mock testnet wallet for you. Click "Request Faucet" to fund it with 10,000 XLM.');
  };

  // Disconnect Wallet
  const handleDisconnect = () => {
    setAddress(null);
    setIsConnected(false);
    setIsMockMode(false);
    setMockSecret(null);
    setRecipient('');
    setAmount('');
    setMemo('');
  };

  // Fund Account via Friendbot (tries Rust backend, falls back directly to Friendbot)
  const handleFaucet = async () => {
    if (!address) return;
    setLoadingFaucet(true);
    try {
      // 1. Try Rust Backend
      const response = await fetch(`${BACKEND_URL}/api/faucet`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          await new Promise(r => setTimeout(r, 1500)); // Brief delay for ledger confirmation
          fetchBalance(address);
          fetchTransactions(address);
        } else {
          throw new Error(data.message);
        }
      } else {
        throw new Error('Backend faucet proxy failed');
      }
    } catch (e) {
      console.log('Rust backend faucet proxy unavailable, requesting Friendbot directly.', e);
      // 2. Direct Friendbot Faucet Fallback
      try {
        const directRes = await fetch(`https://friendbot.stellar.org/?addr=${address}`);
        if (directRes.ok) {
          await new Promise(r => setTimeout(r, 1500));
          fetchBalance(address);
          fetchTransactions(address);
        } else {
          alert('Faucet request failed. Ensure your wallet address is correct.');
        }
      } catch (err: any) {
        console.error('Direct faucet request failed:', err);
        alert(`Faucet request failed: ${err.message}`);
      }
    } finally {
      setLoadingFaucet(false);
    }
  };

  // Copy address to clipboard
  const copyAddress = () => {
    if (!address) return;
    navigator.clipboard.writeText(address);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  // Truncate address for display
  const truncateAddr = (addr: string | null) => {
    if (!addr) return '';
    return `${addr.substring(0, 6)}...${addr.substring(addr.length - 4)}`;
  };

  // Form validations
  const validateForm = (): boolean => {
    let isValid = true;
    setRecipientError('');
    setAmountError('');

    // Recipient address checks
    if (!recipient.trim()) {
      setRecipientError('Recipient address is required.');
      isValid = false;
    } else if (!recipient.startsWith('G') || recipient.length !== 56) {
      setRecipientError('Invalid Stellar public key format. Must be 56 characters starting with G.');
      isValid = false;
    } else if (recipient === address) {
      setRecipientError('Cannot send XLM to your own address.');
      isValid = false;
    }

    // Amount checks
    if (!amount.trim()) {
      setAmountError('Amount is required.');
      isValid = false;
    } else {
      const amtNum = parseFloat(amount);
      if (isNaN(amtNum) || amtNum <= 0) {
        setAmountError('Amount must be a positive number.');
        isValid = false;
      } else if (balance && amtNum >= parseFloat(balance)) {
        setAmountError(`Insufficient balance. Maximum sendable is less than ${balance} XLM (leave some for fee).`);
        isValid = false;
      }
    }

    return isValid;
  };

  // Submit Payment Transaction
  const handleSendPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!address) return;

    if (!validateForm()) return;

    setTxStatus('signing');
    setTxHash(null);
    setTxError(null);

    try {
      // 1. Load source account sequence number
      const sourceAccount = await server.loadAccount(address);

      // 2. Build Transaction Envelope
      const builder = new TransactionBuilder(sourceAccount, {
        fee: '100', // Stroops (0.00001 XLM)
        networkPassphrase: Networks.TESTNET
      })
      .addOperation(
        Operation.payment({
          destination: recipient,
          asset: Asset.native(),
          amount: parseFloat(amount).toFixed(7) // Stellar native amount needs up to 7 decimal precision
        })
      );

      // Optional text memo
      if (memo.trim()) {
        builder.addMemo(Memo.text(memo));
      }

      builder.setTimeout(30);
      const transaction = builder.build();
      
      let signedXdr: string;

      if (isMockMode && mockSecret) {
        // Direct signing using the simulated Keypair in mock mode
        await new Promise(r => setTimeout(r, 1200)); // Simulate wallet prompt delay
        const kp = Keypair.fromSecret(mockSecret);
        transaction.sign(kp);
        signedXdr = transaction.toXDR();
      } else {
        // Prompt user signature in Freighter wallet
        const txXdr = transaction.toXDR();
        const signResult = await signTransaction(txXdr, {
          networkPassphrase: Networks.TESTNET
        });

        // Extract signed XDR from Freighter result object
        if (typeof signResult === 'string') {
          signedXdr = signResult;
        } else if (signResult && signResult.signedTxXdr) {
          signedXdr = signResult.signedTxXdr;
        } else if (signResult && signResult.error) {
          throw new Error(signResult.error.message || signResult.error);
        } else {
          throw new Error('Signing process was rejected or failed.');
        }
      }

      // 4. Submit signed transaction to Horizon network
      setTxStatus('submitting');
      const deserializedTx = new Transaction(signedXdr, Networks.TESTNET);
      const submitResponse = await server.submitTransaction(deserializedTx);

      // 5. Update UI on success
      setTxHash(submitResponse.hash);
      setTxStatus('success');
      
      // Clear inputs
      setRecipient('');
      setAmount('');
      setMemo('');

      // Refresh balance and transaction log
      fetchBalance(address);
      fetchTransactions(address);

    } catch (err: any) {
      console.error('Transaction Submission Failed:', err);
      
      // Check for specific error message details from Horizon response
      let errorMsg = err.message || 'Unknown error occurred.';
      if (err.response && err.response.data && err.response.data.extras && err.response.data.extras.result_codes) {
        const codes = err.response.data.extras.result_codes;
        errorMsg = `Horizon transaction failed: ${codes.transaction} (${codes.operations ? codes.operations.join(', ') : ''})`;
      }

      setTxError(errorMsg);
      setTxStatus('error');
    }
  };

  return (
    <div id="root">
      {/* Header bar */}
      <header className="app-header">
        <div className="logo-section">
          <svg className="logo-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="12 2 2 7 12 12 22 7 12 2" />
            <polyline points="2 17 12 22 22 17" />
            <polyline points="2 12 12 17 22 12" />
          </svg>
          <span className="app-title">Stellar Pay</span>
          {isMockMode ? (
            <span className="network-badge" style={{ background: 'var(--success-light)', color: 'var(--success)', border: '1px solid rgba(52, 211, 153, 0.2)' }}>
              Simulated
            </span>
          ) : (
            <span className="network-badge">Testnet</span>
          )}
        </div>

        <div className="header-actions">
          {/* Light/Dark mode toggle */}
          <button 
            className="theme-toggle" 
            onClick={() => setIsDarkTheme(!isDarkTheme)}
            aria-label="Toggle Theme"
          >
            {isDarkTheme ? <Sun size={20} /> : <Moon size={20} />}
          </button>

          {/* Connect Button */}
          {isConnected ? (
            <button className="wallet-btn connected" onClick={handleDisconnect}>
              {isMockMode ? <Cpu size={16} style={{ color: 'var(--success)' }} /> : <Wallet size={16} />}
              <span>{truncateAddr(address)} {isMockMode && '(Simulated)'}</span>
              <ArrowRight size={14} style={{ marginLeft: '4px' }} />
            </button>
          ) : (
            <button className="wallet-btn" onClick={handleConnect}>
              <Wallet size={16} />
              <span>Connect Freighter</span>
            </button>
          )}
        </div>
      </header>

      {/* Main content grid */}
      <main className="main-container">
        {/* Connection Guidance Banner if not connected */}
        {!isConnected && (
          <div className="full-width-section glass-panel" style={{ textAlign: 'center', padding: '60px 40px' }}>
            <Coins size={64} className="spinner" style={{ color: 'var(--accent)', marginBottom: '24px' }} />
            <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '32px', marginBottom: '16px' }}>
              Welcome to Stellar Pay dApp
            </h1>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto 32px', lineHeight: '1.6' }}>
              Interact with the Stellar Testnet blockchain directly from your browser. 
              Connect your Freighter wallet to check your native XLM balances, fund your account using the Testnet Faucet, and send instant payments.
            </p>
            <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <button className="btn-primary" onClick={handleConnect} style={{ maxWidth: '240px' }}>
                <Wallet size={18} />
                Connect Wallet to Start
              </button>
              <button className="btn-secondary" onClick={handleStartSimulation} style={{ minWidth: '240px' }}>
                <Cpu size={18} style={{ color: 'var(--success)' }} />
                Start Simulated Mode
              </button>
            </div>
          </div>
        )}

        {/* Dashboard Panels (Only visible when connected) */}
        {isConnected && (
          <>
            {/* Left side: Send Payment form */}
            <div className="glass-panel">
              <h2 className="card-title">
                <Send size={18} style={{ color: 'var(--accent)' }} />
                Send Native Payment {isMockMode && '(Simulated Signing)'}
              </h2>

              <form onSubmit={handleSendPayment}>
                {/* Recipient Input */}
                <div className="form-group">
                  <label className="form-label">Recipient Stellar Address</label>
                  <div className="input-container">
                    <span className="input-icon">G</span>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="e.g. GA7YNBW5CBTJZ3ZZOW..."
                      value={recipient}
                      onChange={(e) => setRecipient(e.target.value)}
                    />
                  </div>
                  {recipientError && (
                    <span className="input-error-msg">
                      <XCircle size={14} />
                      {recipientError}
                    </span>
                  )}
                </div>

                {/* Amount Input */}
                <div className="form-group">
                  <label className="form-label">Amount</label>
                  <div className="input-container">
                    <Coins size={16} className="input-icon" />
                    <input 
                      type="number" 
                      step="any"
                      className="form-input" 
                      placeholder="0.0"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                    />
                    <span className="input-suffix">XLM</span>
                  </div>
                  {amountError && (
                    <span className="input-error-msg">
                      <XCircle size={14} />
                      {amountError}
                    </span>
                  )}
                </div>

                {/* Optional Memo Input */}
                <div className="form-group">
                  <label className="form-label">Memo (Optional)</label>
                  <div className="input-container">
                    <Info size={16} className="input-icon" />
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="Transaction note (text)"
                      value={memo}
                      maxLength={28} // Stellar text memo max length is 28 bytes
                      onChange={(e) => setMemo(e.target.value)}
                    />
                  </div>
                </div>

                {/* Send Button */}
                <button type="submit" className="btn-primary" style={{ marginTop: '12px' }}>
                  <Send size={16} />
                  Send XLM Transaction
                </button>
              </form>
            </div>

            {/* Right side: Wallet & Balance info */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
              <div className="glass-panel">
                <h2 className="card-title">
                  {isMockMode ? (
                    <Cpu size={18} style={{ color: 'var(--success)' }} />
                  ) : (
                    <Wallet size={18} style={{ color: 'var(--accent)' }} />
                  )}
                  {isMockMode ? 'Simulated Wallet' : 'Connected Wallet'}
                </h2>

                <div className="balance-display">
                  <span className="balance-label">Your Balance</span>
                  <div className="balance-amount">
                    {loadingBalance ? (
                      <RefreshCw size={36} className="spinner" />
                    ) : (
                      <>
                        {balance !== null ? balance : '0.0000'} 
                        <span className="balance-symbol">XLM</span>
                      </>
                    )}
                  </div>
                  
                  {balance !== null && (
                    <div className="xlm-value-usd">
                      ≈ ${(parseFloat(balance) * xlmUsd).toFixed(2)} USD (at ${xlmUsd.toFixed(3)}/XLM)
                    </div>
                  )}

                  {/* Public Key Display */}
                  <div className="info-banner" style={{ width: '100%', wordBreak: 'break-all', marginBottom: '24px' }}>
                    <div style={{ flex: 1 }}>
                      <strong style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
                        Public Address
                      </strong>
                      <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)' }}>{address}</span>
                      {isMockMode && (
                        <span style={{ fontSize: '10px', color: 'var(--success)', display: 'block', marginTop: '4px', fontWeight: 'bold' }}>
                          🔑 Simulated Private Key is held in session memory.
                        </span>
                      )}
                    </div>
                    <button className="copy-btn" onClick={copyAddress} title="Copy Address">
                      {isCopied ? <Check size={16} style={{ color: 'var(--success)' }} /> : <Copy size={16} />}
                    </button>
                  </div>

                  {/* Actions (Refresh, Faucet) */}
                  <div className="balance-actions">
                    <button 
                      className="btn-secondary" 
                      onClick={() => address && fetchBalance(address)} 
                      disabled={loadingBalance}
                    >
                      <RefreshCw size={14} className={loadingBalance ? 'spinner' : ''} />
                      Refresh
                    </button>
                    <button 
                      className="btn-secondary" 
                      onClick={handleFaucet} 
                      disabled={loadingFaucet}
                    >
                      {loadingFaucet ? (
                        <RefreshCw size={14} className="spinner" />
                      ) : (
                        <Coins size={14} style={{ color: 'var(--success)' }} />
                      )}
                      Request Faucet
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom: Transaction History log */}
            <div className="full-width-section glass-panel">
              <h2 className="card-title" style={{ justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <History size={18} style={{ color: 'var(--accent)' }} />
                  Recent Account Activity (Horizon)
                </div>
                <button 
                  className="btn-secondary" 
                  onClick={() => address && fetchTransactions(address)}
                  disabled={loadingTx}
                  style={{ minWidth: 'auto', padding: '6px 12px', fontSize: '12px' }}
                >
                  <RefreshCw size={12} className={loadingTx ? 'spinner' : ''} />
                  Sync
                </button>
              </h2>

              {loadingTx && transactions.length === 0 ? (
                <div className="empty-state">
                  <RefreshCw size={36} className="spinner" />
                  <p>Syncing recent transactions with Horizon Testnet...</p>
                </div>
              ) : transactions.length === 0 ? (
                <div className="empty-state">
                  <History className="empty-state-icon" />
                  <p style={{ fontWeight: 600 }}>No payments found for this account</p>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    Transactions will appear here once you send or receive payments on the Testnet.
                  </p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="tx-table">
                    <thead>
                      <tr>
                        <th>Direction</th>
                        <th>Address</th>
                        <th>Amount</th>
                        <th>Asset</th>
                        <th>Time</th>
                        <th>Explorer</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((tx) => {
                        const isSent = tx.from === address;
                        const oppositeAddr = isSent ? tx.to : tx.from;
                        return (
                          <tr key={tx.id}>
                            <td>
                              <span className={`status-badge ${isSent ? 'sent' : 'received'}`}>
                                {isSent ? 'Sent' : 'Received'}
                              </span>
                            </td>
                            <td>
                              <a 
                                href={`https://stellar.expert/explorer/testnet/account/${oppositeAddr}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="address-link"
                              >
                                {truncateAddr(oppositeAddr)}
                              </a>
                            </td>
                            <td style={{ fontWeight: '600', color: isSent ? 'var(--error)' : 'var(--success)' }}>
                              {isSent ? '-' : '+'}{parseFloat(tx.amount).toFixed(2)}
                            </td>
                            <td>{tx.asset_type === 'native' ? 'XLM' : 'Token'}</td>
                            <td style={{ color: 'var(--text-secondary)' }}>
                              {new Date(tx.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                            </td>
                            <td>
                              <a 
                                href={`https://stellar.expert/explorer/testnet/tx/${tx.transaction_hash}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="address-link"
                                style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                              >
                                View <ExternalLink size={12} />
                              </a>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </main>

      {/* Footer information */}
      <footer className="app-footer">
        <p>
          Stellar Journey to Mastery - Level 1 (White Belt) | Built with{' '}
          <a href="https://react.dev" target="_blank" rel="noreferrer" className="footer-link">React</a>,{' '}
          <a href="https://rust-lang.org" target="_blank" rel="noreferrer" className="footer-link">Rust</a> &{' '}
          <a href="https://python.org" target="_blank" rel="noreferrer" className="footer-link">Python</a>
        </p>
      </footer>

      {/* Transaction status feedback overlay modal */}
      {txStatus !== 'idle' && (
        <div className="modal-overlay">
          <div className="modal-content">
            {txStatus === 'signing' && (
              <>
                <div className="modal-icon-container loading">
                  <RefreshCw size={32} className="spinner" />
                </div>
                <h3 className="modal-title">{isMockMode ? 'Simulating Signing...' : 'Sign with Freighter'}</h3>
                <p className="modal-text">
                  {isMockMode 
                    ? 'Signing the transaction envelope using the session mock keypair...' 
                    : 'Please open your Freighter wallet extension popup to authorize and sign the transaction envelope.'}
                </p>
              </>
            )}

            {txStatus === 'submitting' && (
              <>
                <div className="modal-icon-container loading">
                  <RefreshCw size={32} className="spinner" />
                </div>
                <h3 className="modal-title">Submitting to Network</h3>
                <p className="modal-text">
                  Your signed transaction is being submitted and confirmed on the Stellar Horizon Testnet.
                </p>
              </>
            )}

            {txStatus === 'success' && (
              <>
                <div className="modal-icon-container success">
                  <CheckCircle2 size={32} />
                </div>
                <h3 className="modal-title" style={{ color: 'var(--success)' }}>Transaction Successful!</h3>
                <p className="modal-text">
                  Your payment has been successfully written to the ledger on the Stellar testnet.
                </p>
                {txHash && (
                  <>
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', fontWeight: '700', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                      Transaction Hash
                    </span>
                    <div className="tx-hash-box">{txHash}</div>
                    <a 
                      href={`https://stellar.expert/explorer/testnet/tx/${txHash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-primary"
                      style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '12px' }}
                    >
                      View on StellarExpert <ExternalLink size={16} />
                    </a>
                  </>
                )}
                <button 
                  className="btn-secondary" 
                  onClick={() => setTxStatus('idle')}
                  style={{ width: '100%' }}
                >
                  Done
                </button>
              </>
            )}

            {txStatus === 'error' && (
              <>
                <div className="modal-icon-container error">
                  <XCircle size={32} />
                </div>
                <h3 className="modal-title" style={{ color: 'var(--error)' }}>Transaction Failed</h3>
                <p className="modal-text">
                  An error occurred while building, signing, or submitting your transaction.
                </p>
                <div 
                  className="tx-hash-box" 
                  style={{ 
                    border: '1px solid rgba(239, 68, 68, 0.2)', 
                    background: 'var(--error-light)', 
                    color: 'var(--error)',
                    textAlign: 'left'
                  }}
                >
                  {txError}
                </div>
                <button 
                  className="btn-primary" 
                  onClick={() => setTxStatus('idle')}
                >
                  Close & Retry
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
