# 💳 Digital E-Wallet System for Visually Impaired Using a Voice Assistant

A secure, accessible, and user-friendly digital e-wallet web application tailored specifically for visually impaired individuals. This system integrates an interactive **Voice Assistant** to allow seamless hands-free navigation, audio feedback, and financial transactions.

---

## 🚀 Features

* **🎙️ Voice Assistant Integration:** Complete audio navigation and feedback to guide users through account balances, transfers, and transaction histories without relying on sight.
* **🔒 Secure User Authentication:** Encrypted login and registration system protecting user credentials and financial data.
* **💰 Digital Wallet Operations:** 
  * Check account balances.
  * Send/transfer funds securely.
  * View real-time transaction history logs.
* **🗄️ Relational Database Backend:** Structured schema using SQL for tracking users, wallets, and transaction histories.

---

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3, JavaScript (`index.html`, `app.js`)
* **Backend:** Node.js / Express (`server.js`)
* **Database:** SQL (`schema.sql`)
* **Environment Configuration:** Dotenv (`.env`)

---

## 📂 Project Structure

```text
DIGITAL-E-WALLET-SYSTEM-FOR-VISUALLY-IMPAIRED/
│
├── .env                  # Environment variables & configurations
├── README.md             # Project documentation
├── app.js                # Frontend scripts & voice assistant logic
├── index.html            # Main user interface
├── package.json          # Node.js dependencies & scripts
├── package-lock.json     # Locked dependency versions
├── schema.sql            # Database schema setup
└── server.js             # Backend server configuration & API routes
