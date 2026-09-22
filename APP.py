import os
import csv
from flask import Flask, render_template_string, request, redirect, url_for, flash, session

USERS_CSV = "wallet_users.csv"
TRANSACTIONS_CSV = "wallet_transactions.csv"

def init_wallet_csv_files():
    if not os.path.exists(USERS_CSV):
        with open(USERS_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "email", "mobile", "pin", "balance", "voice_print"])

    if not os.path.exists(TRANSACTIONS_CSV):
        with open(TRANSACTIONS_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["email", "tx_id", "type", "amount", "target", "timestamp"])

init_wallet_csv_files()

def save_user_to_csv(name, email, mobile, pin, balance=0.0, voice_print="Enabled"):
    if find_user_by_email(email):
        return False, "Email already registered in wallet."
    with open(USERS_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([name, email, mobile, pin, balance, voice_print])
    return True, "Wallet account created successfully."

def find_user_by_email(email):
    if not os.path.exists(USERS_CSV):
        return None
    with open(USERS_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["email"].strip().lower() == email.strip().lower():
                if "voice_print" not in row:
                    row["voice_print"] = "Enabled"
                return row
    return None

def update_user_balance_in_csv(email, new_balance, tx_record=None):
    rows = []
    fieldnames = ["name", "email", "mobile", "pin", "balance", "voice_print"]
    if os.path.exists(USERS_CSV):
        with open(USERS_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "voice_print" not in row:
                    row["voice_print"] = "Enabled"
                if row["email"].strip().lower() == email.strip().lower():
                    row["balance"] = str(new_balance)
                rows.append(row)

    with open(USERS_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    if tx_record:
        with open(TRANSACTIONS_CSV, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                email,
                tx_record["tx_id"],
                tx_record["type"],
                tx_record["amount"],
                tx_record["target"],
                tx_record["timestamp"]
            ])

def get_user_transactions(email):
    txs = []
    if os.path.exists(TRANSACTIONS_CSV):
        with open(TRANSACTIONS_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["email"].strip().lower() == email.strip().lower():
                    txs.append(row)
    return list(reversed(txs))
app = Flask(__name__)
app.secret_key = "paypulse_secure_random_flask_key"

TEMPLATE_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PayPulse Accessible Digital Wallet for Visually Impaired</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <style>
        body { background-color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 1.1rem; }
        body.dark-mode { background-color: #0b0f19; color: #f8fafc; }
        body.dark-mode .card { background-color: #1e293b; color: #f8fafc; border: 2px solid #64748b; }
        body.dark-mode .table { color: #f8fafc; }
        body.dark-mode .table-light { background-color: #334155; color: #f8fafc; }
        body.dark-mode .form-control, body.dark-mode .form-select { background-color: #0f172a; color: #fff; border-color: #64748b; }
        
        a:focus, button:focus, input:focus, select:focus {
            outline: 4px solid #2563eb !important;
            outline-offset: 2px !important;
        }

        .card { border-radius: 12px; box-shadow: 0 6px 12px rgba(0,0,0,0.15); border: 2px solid #cbd5e1; }
        .balance-card { background: linear-gradient(135deg, #1e40af, #1d4ed8); color: white; border: 3px solid #60a5fa; }
        
        .voice-orb {
            width: 85px; height: 85px; background: linear-gradient(135deg, #7c3aed, #a855f7);
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
            color: white; font-size: 2.2rem; cursor: pointer; box-shadow: 0 0 25px rgba(124, 58, 237, 0.7);
            transition: transform 0.2s, box-shadow 0.2s; border: 3px solid #fff;
        }
        .voice-orb.listening {
            animation: pulse-ring 1.5s infinite;
            background: linear-gradient(135deg, #dc2626, #ef4444);
        }
        @keyframes pulse-ring {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.8); }
            70% { transform: scale(1.15); box-shadow: 0 0 0 20px rgba(220, 38, 38, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
        }
        .tab-pane-content { display: none; }
        .tab-pane-content.active-pane { display: block; }
    </style>
</head>
<body>
    <div class="container py-4">
        <div class="visually-hidden" aria-live="polite" id="screenReaderAnnouncer"></div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show fw-bold" role="alert" aria-live="assertive">
                        <i class="bi bi-info-circle-fill me-2"></i> {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% if not session.get('user_email') %}
            <!-- AUTHENTICATION VIEW -->
            <div class="row justify-content-center mt-3">
                <div class="col-md-7">
                    <div class="text-center mb-4">
                        <h1 class="fw-bold text-primary display-6"><i class="bi bi-wallet2"></i> PayPulse Voice Wallet</h1>
                        <p class="text-muted fs-5">Fully Accessible Digital E-Wallet for Visually Impaired Users</p>
                        <button class="btn btn-lg btn-outline-purple fw-bold shadow-sm" style="background-color: #f3e8ff; color: #6b21a8; border: 2px solid #c084fc;" onclick="startInteractiveAssistant()">
                            <i class="bi bi-mic-fill"></i> Click to Start Voice Assistant
                        </button>
                    </div>
                    <div class="card p-4">
                        <div class="d-flex gap-2 mb-4">
                            <button class="btn btn-primary flex-fill fw-bold fs-5 py-2" id="authLoginBtn" onclick="switchAuthMode('login')">🔑 Login</button>
                            <button class="btn btn-outline-secondary flex-fill fw-bold fs-5 py-2" id="authRegBtn" onclick="switchAuthMode('register')">📝 Register</button>
                        </div>
                        
                        <div id="authLoginPane">
                            <form method="POST" action="{{ url_for('login') }}" id="loginFormElement">
                                <div class="mb-3">
                                    <label class="form-label fw-bold">Email Address</label>
                                    <input type="email" class="form-control form-control-lg" id="loginEmail" name="email" placeholder="name@example.com" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label fw-bold">4-Digit Security PIN</label>
                                    <input type="password" class="form-control form-control-lg" id="loginPin" name="pin" maxlength="4" placeholder="••••" required>
                                </div>
                                <button type="submit" class="btn btn-primary btn-lg w-100 fw-bold mb-3">Login to Wallet</button>
                            </form>
                        </div>
                        
                        <div id="authRegisterPane" style="display: none;">
                            <form method="POST" action="{{ url_for('register') }}" id="registerFormElement">
                                <div class="mb-3">
                                    <label class="form-label fw-bold">Full Name</label>
                                    <input type="text" class="form-control form-control-lg" id="regName" name="name" placeholder="John Doe" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label fw-bold">Mobile Number</label>
                                    <input type="text" class="form-control form-control-lg" id="regMobile" name="mobile" maxlength="10" placeholder="10-digit mobile" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label fw-bold">Email Address</label>
                                    <input type="email" class="form-control form-control-lg" id="regEmail" name="email" placeholder="name@example.com" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label fw-bold">Set 4-Digit PIN</label>
                                    <input type="password" class="form-control form-control-lg" id="regPin" name="pin" maxlength="4" placeholder="••••" required>
                                </div>
                                <button type="submit" class="btn btn-success btn-lg w-100 fw-bold">Create Wallet Account</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        {% else %}
            <!-- DASHBOARD VIEW -->
            <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
                <div>
                    <h2 class="fw-bold text-primary mb-0"><i class="bi bi-wallet2"></i> PayPulse Dashboard</h2>
                    <span class="badge bg-success fs-6 mt-1">Voice Assistant Active & Ready</span>
                </div>
                <div class="d-flex align-items-center gap-2">
                    <button class="btn btn-outline-dark fw-bold" onclick="toggleDarkMode()">
                        <i class="bi bi-moon-stars-fill" id="darkModeIcon"></i> Contrast
                    </button>
                    <span class="fw-bold text-secondary">👤 {{ user.name }}</span>
                    <a href="{{ url_for('logout') }}" class="btn btn-danger fw-bold">Logout</a>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-md-6 mb-3">
                    <div class="card balance-card p-4 h-100">
                        <span class="text-white-50 fs-5">Available Wallet Balance</span>
                        <h1 class="display-4 fw-bold mb-3" id="balanceDisplay" aria-live="polite">₹ {{ "%.2f"|format(user.balance|float) }}</h1>
                        <div class="mt-auto d-flex gap-2">
                            <button class="btn btn-light text-primary fw-bold" onclick="speakBalance()">🔊 Read Balance</button>
                            <span class="badge bg-success text-white align-self-center fs-6">Voice Biometrics Verified</span>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 mb-3">
                    <div class="card p-4 h-100">
                        <h5 class="fw-bold mb-3"><i class="bi bi-mic"></i> Voice Command Shortcuts</h5>
                        <ul class="text-muted fs-6 mb-0 ps-3">
                            <li>Say <strong>"Hey Wallet"</strong> anytime to activate voice control.</li>
                            <li>Say <strong>"Send money"</strong> (requires PIN confirmation).</li>
                            <li>Say <strong>"Recharge"</strong> or <strong>"Add money"</strong>.</li>
                            <li>Say <strong>"Read history"</strong> for recent transactions.</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="d-flex flex-wrap gap-2 mb-4">
                <button class="btn btn-primary fw-bold fs-5 px-4 py-2 dashboard-tab-btn" id="btnTabTransfer" onclick="switchDashboardTab('paneTransfer')"><i class="bi bi-send"></i> Send Money</button>
                <button class="btn btn-outline-primary fw-bold fs-5 px-4 py-2 dashboard-tab-btn" id="btnTabRecharge" onclick="switchDashboardTab('paneRecharge')"><i class="bi bi-phone"></i> Recharge</button>
                <button class="btn btn-outline-primary fw-bold fs-5 px-4 py-2 dashboard-tab-btn" id="btnTabDeposit" onclick="switchDashboardTab('paneDeposit')"><i class="bi bi-plus-circle"></i> Add Funds</button>
                <button class="btn btn-outline-primary fw-bold fs-5 px-4 py-2 dashboard-tab-btn" id="btnTabHistory" onclick="switchDashboardTab('paneHistory')"><i class="bi bi-file-text"></i> History</button>
            </div>

            <div class="card p-4">
                <div class="tab-pane-content active-pane" id="paneTransfer">
                    <h3 class="fw-bold mb-3">Transfer Funds</h3>
                    <form method="POST" action="{{ url_for('transfer') }}" id="transferFormElement" class="col-md-7">
                        <div class="mb-3">
                            <label class="form-label fw-bold">Recipient Mobile / UPI ID</label>
                            <input type="text" class="form-control form-control-lg" id="transferTarget" name="target" placeholder="e.g. 9876543210" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Amount (₹)</label>
                            <input type="number" step="0.01" class="form-control form-control-lg" id="transferAmount" name="amount" value="100.00" min="1" required>
                        </div>
                        <button type="submit" class="btn btn-success btn-lg fw-bold w-100">Send Money Securely</button>
                    </form>
                </div>

                <div class="tab-pane-content" id="paneRecharge">
                    <h3 class="fw-bold mb-3">Mobile & Utility Recharge</h3>
                    <form method="POST" action="{{ url_for('recharge') }}" id="rechargeFormElement" class="col-md-7">
                        <div class="mb-3">
                            <label class="form-label fw-bold">Operator / Service</label>
                            <select class="form-select form-select-lg" id="rechargeOperator" name="operator">
                                <option>Jio Prepaid</option>
                                <option>Airtel Prepaid</option>
                                <option>Vi Prepaid</option>
                                <option>BSNL Recharge</option>
                                <option>Electricity Bill</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Consumer / Mobile Number</label>
                            <input type="text" class="form-control form-control-lg" id="rechargeNumber" name="number" placeholder="Enter mobile number" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Amount (₹)</label>
                            <input type="number" step="0.01" class="form-control form-control-lg" id="rechargeAmount" name="amount" value="299.00" min="10" required>
                        </div>
                        <button type="submit" class="btn btn-primary btn-lg fw-bold w-100">Proceed to Recharge</button>
                    </form>
                </div>

                <div class="tab-pane-content" id="paneDeposit">
                    <h3 class="fw-bold mb-3">Add Funds to Wallet</h3>
                    <form method="POST" action="{{ url_for('deposit') }}" id="depositFormElement" class="col-md-7">
                        <div class="mb-3">
                            <label class="form-label fw-bold">Funding Source</label>
                            <select class="form-select form-select-lg" id="depositSource" name="source">
                                <option>HDFC Bank A/c</option>
                                <option>SBI Bank A/c</option>
                                <option>Google Pay UPI</option>
                                <option>Credit / Debit Card</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Deposit Amount (₹)</label>
                            <input type="number" step="0.01" class="form-control form-control-lg" id="depositAmount" name="amount" value="1000.00" min="10" required>
                        </div>
                        <button type="submit" class="btn btn-primary btn-lg fw-bold w-100">Top Up Wallet Balance</button>
                    </form>
                </div>

                <div class="tab-pane-content" id="paneHistory">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h3 class="fw-bold mb-0">Transaction History</h3>
                        <button class="btn btn-outline-primary fw-bold" onclick="speakHistory()"><i class="bi bi-volume-up-fill"></i> Read History Aloud</button>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle fs-6">
                            <thead class="table-light">
                                <tr>
                                    <th>Transaction ID</th>
                                    <th>Type</th>
                                    <th>Amount</th>
                                    <th>Target / Source</th>
                                    <th>Timestamp</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for tx in transactions %}
                                <tr class="tx-row" data-type="{{ tx.type }}" data-amount="{{ tx.amount }}" data-target="{{ tx.target }}">
                                    <td><code>{{ tx.tx_id }}</code></td>
                                    <td><span class="badge bg-{{ 'success' if tx.type == 'Deposit' else 'secondary' }} fs-6">{{ tx.type }}</span></td>
                                    <td class="fw-bold">₹ {{ "%.2f"|format(tx.amount|float) }}</td>
                                    <td>{{ tx.target }}</td>
                                    <td class="text-muted">{{ tx.timestamp }}</td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="5" class="text-center text-muted py-4">No transactions recorded yet.</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        {% endif %}
    </div>

    <div style="position: fixed; bottom: 30px; right: 30px; z-index: 1050; text-align: center;">
        <div class="voice-orb" id="voiceOrb" onclick="startInteractiveAssistant()" title="Click to talk to Voice Assistant">
            <i class="bi bi-mic-fill" id="micIcon"></i>
        </div>
        <div id="voiceStatusBadge" class="badge bg-dark text-white p-2 mt-2 shadow rounded-pill fs-6" style="display: none;" aria-live="polite">Ready</div>
    </div>

    <script>
        function toggleDarkMode() {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            document.getElementById('darkModeIcon').className = isDark ? 'bi bi-sun-fill text-warning' : 'bi bi-moon-stars-fill';
            speakText(isDark ? "High contrast mode enabled." : "High contrast mode disabled.");
        }

        function switchAuthMode(mode) {
            if (mode === 'login') {
                document.getElementById('authLoginPane').style.display = 'block';
                document.getElementById('authRegisterPane').style.display = 'none';
                document.getElementById('authLoginBtn').className = 'btn btn-primary flex-fill fw-bold fs-5 py-2';
                document.getElementById('authRegBtn').className = 'btn btn-outline-secondary flex-fill fw-bold fs-5 py-2';
                speakText("Switched to login mode.");
            } else {
                document.getElementById('authLoginPane').style.display = 'none';
                document.getElementById('authRegisterPane').style.display = 'block';
                document.getElementById('authLoginBtn').className = 'btn btn-outline-secondary flex-fill fw-bold fs-5 py-2';
                document.getElementById('authRegBtn').className = 'btn btn-success flex-fill fw-bold fs-5 py-2';
                speakText("Switched to registration mode.");
            }
        }

        function switchDashboardTab(paneId) {
            const panes = document.querySelectorAll('.tab-pane-content');
            panes.forEach(pane => pane.classList.remove('active-pane'));
            
            const targetPane = document.getElementById(paneId);
            if (targetPane) targetPane.classList.add('active-pane');

            const buttons = document.querySelectorAll('.dashboard-tab-btn');
            buttons.forEach(btn => {
                btn.className = 'btn btn-outline-primary fw-bold fs-5 px-4 py-2 dashboard-tab-btn';
            });
            
            if (paneId === 'paneTransfer') document.getElementById('btnTabTransfer').className = 'btn btn-primary fw-bold fs-5 px-4 py-2 dashboard-tab-btn';
            if (paneId === 'paneRecharge') document.getElementById('btnTabRecharge').className = 'btn btn-primary fw-bold fs-5 px-4 py-2 dashboard-tab-btn';
            if (paneId === 'paneDeposit') document.getElementById('btnTabDeposit').className = 'btn btn-primary fw-bold fs-5 px-4 py-2 dashboard-tab-btn';
            if (paneId === 'paneHistory') document.getElementById('btnTabHistory').className = 'btn btn-primary fw-bold fs-5 px-4 py-2 dashboard-tab-btn';
        }

        function speakText(text, onEndCallback) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'en-IN';
                utterance.rate = 1.0;
                if (onEndCallback) utterance.onend = onEndCallback;
                window.speechSynthesis.speak(utterance);
            } else if (onEndCallback) {
                onEndCallback();
            }
        }

        function speakBalance() {
            {% if session.get('user_email') %}
            const bal = "{{ user.balance }}";
            speakText(`Your current available balance is ${bal} rupees.`);
            {% endif %}
        }

        function speakHistory() {
            const rows = document.querySelectorAll('.tx-row');
            if (rows.length === 0) {
                speakText("You have no transactions recorded yet.");
                return;
            }
            let summaryText = `You have ${rows.length} recent transactions. `;
            let count = 0;
            rows.forEach((row, idx) => {
                if (count < 3) {
                    const type = row.getAttribute('data-type');
                    const amount = row.getAttribute('data-amount');
                    const target = row.getAttribute('data-target');
                    summaryText += `Transaction ${idx + 1}: ${type} of ${amount} rupees for ${target}. `;
                    count++;
                }
            });
            speakText(summaryText);
        }

        let currentFlow = null;       
        let loginStep = 0;   
        let txStep = 0;      // 0: target, 1: amount, 2: PIN confirmation
        let rechargeStep = 0;

        let recognition;
        let isListening = false;
        let isWakeWordMode = true;

        function initWakeWordListener() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = false;
            recognition.lang = 'en-IN';

            const orb = document.getElementById('voiceOrb');
            const badge = document.getElementById('voiceStatusBadge');

            recognition.onstart = function() {
                isListening = true;
                if (!currentFlow) {
                    orb.classList.add('listening');
                    badge.style.display = 'block';
                    badge.innerHTML = "🎙️ Listening for 'Hey Wallet'...";
                }
            };

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript.trim().toLowerCase();
                badge.innerHTML = `🗣️ "${transcript}"`;

                if (!currentFlow && (transcript.includes('hey wallet') || transcript.includes('hi wallet'))) {
                    speakText("Voice wallet activated. How can I help you?", () => {
                        startInteractiveAssistantSession();
                    });
                } else if (currentFlow) {
                    handleConversation(transcript);
                }
            };

            recognition.onerror = function() {
                if (isWakeWordMode && !currentFlow) {
                    try { recognition.start(); } catch(e) {}
                }
            };

            recognition.onend = function() {
                if (isWakeWordMode && !currentFlow) {
                    try { recognition.start(); } catch (e) {
                        isListening = false;
                        orb.classList.remove('listening');
                    }
                } else {
                    stopListeningState();
                }
            };

            try { recognition.start(); } catch(e) {}
        }

        function startInteractiveAssistantSession() {
            isWakeWordMode = false;
            if (recognition) {
                try { recognition.stop(); } catch(e) {}
            }
            setTimeout(() => { startInteractiveAssistant(); }, 500);
        }

        function startInteractiveAssistant() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert("Speech recognition is not supported in this browser. Please use Google Chrome.");
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-IN';

            const orb = document.getElementById('voiceOrb');
            const badge = document.getElementById('voiceStatusBadge');

            recognition.onstart = function() {
                isListening = true;
                orb.classList.add('listening');
                badge.style.display = 'block';
                badge.innerHTML = "🎙️ Listening...";
            };

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript.trim();
                badge.innerHTML = `🗣️ "${transcript}"`;
                handleConversation(transcript);
            };

            recognition.onerror = function() {
                badge.innerHTML = "⚠️ Error hearing voice";
                speakText("Sorry, I didn't catch that. Please try again.");
                stopListeningState();
            };

            recognition.onend = function() {
                stopListeningState();
                // Resume wake word listening after short interaction completes
                if (!currentFlow) {
                    isWakeWordMode = true;
                    setTimeout(initWakeWordListener, 1000);
                }
            };

            {% if not session.get('user_email') %}
                if (!currentFlow) {
                    currentFlow = 'login';
                    loginStep = 0;
                    speakText("Let's log in. Please say your email address.", () => { recognition.start(); });
                    return;
                }
            {% else %}
                if (!currentFlow) {
                    recognition.start();
                    return;
                }
            {% endif %}

            if (!isListening) {
                recognition.start();
            } else {
                recognition.stop();
            }
        }

        function stopListeningState() {
            isListening = false;
            const orb = document.getElementById('voiceOrb');
            if (orb) orb.classList.remove('listening');
        }

        function handleConversation(input) {
            const lowerInput = input.toLowerCase();

            {% if not session.get('user_email') %}
                if (currentFlow === 'login') {
                    if (loginStep === 0) {
                        let cleanEmail = input.replace(/\s+/g, '').replace(/at/gi, '@').replace(/dot/gi, '.');
                        document.getElementById('loginEmail').value = cleanEmail;
                        loginStep = 1;
                        speakText("Got email. Now please say your 4-digit security PIN.", () => { recognition.start(); });
                    } else if (loginStep === 1) {
                        let pinInput = input.replace(/\D/g, '').slice(0, 4);
                        document.getElementById('loginPin').value = pinInput;
                        speakText("Verifying login. Logging you in now.", () => {
                            document.getElementById('loginFormElement').submit();
                        });
                        currentFlow = null;
                    }
                }
            {% else %}
                if (!currentFlow) {
                    if (lowerInput.includes('add') || lowerInput.includes('deposit') || lowerInput.includes('top up')) {
                        currentFlow = 'deposit';
                        switchDashboardTab('paneDeposit');
                        speakText("How much money would you like to add?", () => { recognition.start(); });
                        return;
                    } else if (lowerInput.includes('send') || lowerInput.includes('transfer')) {
                        currentFlow = 'transfer';
                        txStep = 0;
                        switchDashboardTab('paneTransfer');
                        speakText("Who would you like to send money to? Say the recipient mobile number.", () => { recognition.start(); });
                        return;
                    } else if (lowerInput.includes('recharge') || lowerInput.includes('bill')) {
                        currentFlow = 'recharge';
                        rechargeStep = 0;
                        switchDashboardTab('paneRecharge');
                        speakText("Say the mobile or consumer number for the recharge.", () => { recognition.start(); });
                        return;
                    } else if (lowerInput.includes('history')) {
                        speakHistory();
                        return;
                    } else if (lowerInput.includes('balance')) {
                        speakBalance();
                        return;
                    } else {
                        speakText("I didn't understand. You can say add money, send money, recharge, or balance.");
                        return;
                    }
                }

                if (currentFlow === 'transfer') {
                    if (txStep === 0) {
                        document.getElementById('transferTarget').value = input.replace(/\s+/g, '');
                        txStep = 1;
                        speakText("How much money would you like to send?", () => { recognition.start(); });
                    } else if (txStep === 1) {
                        const matches = input.match(/\d+/g);
                        let amt = matches ? matches[0] : "100";
                        document.getElementById('transferAmount').value = amt;
                        txStep = 2;
                        speakText(`You are sending ${amt} rupees. Please say your 4-digit security PIN to confirm and complete the transfer.`, () => { recognition.start(); });
                    } else if (txStep === 2) {
                        speakText("PIN received. Processing transfer securely.", () => {
                            document.getElementById('transferFormElement').submit();
                        });
                        currentFlow = null;
                    }
                }
                else if (currentFlow === 'recharge') {
                    if (rechargeStep === 0) {
                        document.getElementById('rechargeNumber').value = input.replace(/\D/g, '');
                        rechargeStep = 1;
                        speakText("How much is the recharge amount?", () => { recognition.start(); });
                    } else if (rechargeStep === 1) {
                        const matches = input.match(/\d+/g);
                        let amt = matches ? matches[0] : "299";
                        document.getElementById('rechargeAmount').value = amt;
                        speakText(`Processing recharge of ${amt} rupees.`, () => {
                            document.getElementById('rechargeFormElement').submit();
                        });
                        currentFlow = null;
                    }
                }
                else if (currentFlow === 'deposit') {
                    const matches = input.match(/\d+/g);
                    let amt = matches ? matches[0] : "500";
                    document.getElementById('depositAmount').value = amt;
                    speakText(`Adding ${amt} rupees to your wallet.`, () => {
                        document.getElementById('depositFormElement').submit();
                    });
                    currentFlow = null;
                }
            {% endif %}
        }

        window.addEventListener('load', () => {
            initWakeWordListener();
            {% if session.get('user_email') %}
                speakBalance();
            {% else %}
                speakText("Welcome to PayPulse Voice Wallet. Say 'Hey Wallet' or click the microphone to begin.");
            {% endif %}
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    user = None
    transactions = []
    if "user_email" in session:
        user = find_user_by_email(session["user_email"])
        if user:
            transactions = get_user_transactions(user["email"])
    return render_template_string(TEMPLATE_HTML, user=user, transactions=transactions)


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    mobile = request.form.get("mobile", "").strip()
    email = request.form.get("email", "").strip()
    pin = request.form.get("pin", "").strip()

    if not name or len(mobile) < 10 or not email or len(pin) != 4:
        flash("Please fill out all fields accurately. PIN must be 4 digits.", "error")
        return redirect(url_for("index"))

    success, msg = save_user_to_csv(name, email, mobile, pin, balance=0.0, voice_print="Enabled")
    if success:
        session["user_email"] = email
        flash("Account created successfully with voice biometrics!", "success")
    else:
        flash(msg, "error")
    return redirect(url_for("index"))


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip()
    pin = request.form.get("pin", "").strip()

    user = find_user_by_email(email)
    if user and user["pin"] == pin:
        session["user_email"] = user["email"]
        flash("Logged in successfully!", "success")
    else:
        flash("Invalid email address or security PIN.", "error")
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("user_email", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))


@app.route("/transfer", methods=["POST"])
def transfer():
    if "user_email" not in session:
        return redirect(url_for("index"))

    user = find_user_by_email(session["user_email"])
    current_balance = float(user["balance"])
    target = request.form.get("target", "").strip()
    try:
        amount = float(request.form.get("amount", 0))
    except ValueError:
        amount = 0.0

    if not target or amount <= 0:
        flash("Invalid target or amount specified.", "error")
        return redirect(url_for("index"))

    if amount > current_balance:
        flash("Insufficient funds in wallet for this transaction.", "error")
        return redirect(url_for("index"))

    new_balance = current_balance - amount
    tx_record = {
        "tx_id": f"TXN{os.urandom(3).hex().upper()}",
        "type": "Transfer",
        "amount": amount,
        "target": target,
        "timestamp": "2026-09-15 20:00:00"
    }
    update_user_balance_in_csv(user["email"], new_balance, tx_record)
    flash(f"Successfully transferred ₹{amount:,.2f} to {target}!", "success")
    return redirect(url_for("index"))


@app.route("/recharge", methods=["POST"])
def recharge():
    if "user_email" not in session:
        return redirect(url_for("index"))

    user = find_user_by_email(session["user_email"])
    current_balance = float(user["balance"])
    operator = request.form.get("operator", "").strip()
    number = request.form.get("number", "").strip()
    try:
        amount = float(request.form.get("amount", 0))
    except ValueError:
        amount = 0.0

    if not number or amount <= 0:
        flash("Please enter a valid mobile number.", "error")
        return redirect(url_for("index"))

    if amount > current_balance:
        flash("Insufficient funds in wallet for this recharge.", "error")
        return redirect(url_for("index"))

    new_balance = current_balance - amount
    tx_record = {
        "tx_id": f"TXN{os.urandom(3).hex().upper()}",
        "type": "Mobile Recharge",
        "amount": amount,
        "target": f"{operator} ({number})",
        "timestamp": "2026-09-15 20:00:00"
    }
    update_user_balance_in_csv(user["email"], new_balance, tx_record)
    flash(f"Successfully completed {operator} recharge of ₹{amount:,.2f}!", "success")
    return redirect(url_for("index"))


@app.route("/deposit", methods=["POST"])
def deposit():
    if "user_email" not in session:
        return redirect(url_for("index"))

    user = find_user_by_email(session["user_email"])
    current_balance = float(user["balance"])
    source = request.form.get("source", "").strip()
    try:
        amount = float(request.form.get("amount", 0))
    except ValueError:
        amount = 0.0

    if amount <= 0:
        flash("Please enter a valid deposit amount.", "error")
        return redirect(url_for("index"))

    new_balance = current_balance + amount
    tx_record = {
        "tx_id": f"TXN{os.urandom(3).hex().upper()}",
        "type": "Deposit",
        "amount": amount,
        "target": source,
        "timestamp": "2026-09-15 20:00:00"
    }
    update_user_balance_in_csv(user["email"], new_balance, tx_record)
    flash(f"Successfully added ₹{amount:,.2f} from {source}!", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)