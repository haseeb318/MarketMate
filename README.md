# ⚡ MarketMate — Autonomous AI Marketing Studio for E-Commerce

[![Streamlit](https://img.shields.io/badge/Streamlit-1.64.0-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-orange?style=for-the-badge)](https://crewai.com)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**MarketMate** is an autonomous, multi-agent AI marketing pipeline tailored for e-commerce. It connects directly to live retail data (sales trends, margins, inventory, and upcoming events) to generate data-backed, bilingual marketing campaigns with deterministic, application-level safety guards and a human-in-the-loop approval dashboard.

---

## 🎯 The Problem

1. **Operational Time Drain:** Retailers spend hours manually analyzing sales spreadsheets, calculating margins, and drafting ad copy across multiple social platforms.
2. **The LLM Hallucination Risk:** Generic AI tools lack real-time inventory awareness—they frequently invent false discounts (e.g. *"50% off!"*), promote out-of-stock items, or fabricate urgency (*"Only 2 left!"*).
3. **The Localization Gap:** Generic copy generators lack cultural nuance and regional appeal (such as authentic **Roman Urdu** for Pakistani e-commerce).
4. **Lack of Governance:** Direct-to-publish automation risks brand reputation if an agent makes an unauthorized promotional promise.

---

## 💡 The Solution

MarketMate solves this with an end-to-end governed pipeline:
* **Real-time Database Grounding:** Agents query live SQLite database tables (`products`, `orders`, `events`) before making any claims.
* **4-Agent Collaborative Crew:** Specialized roles handle sales analysis, strategy, bilingual copywriting, and schedule coordination.
* **Deterministic Safety Middleware:** Python & DB validation gates intercept and block invalid posts before they can enter the database.
* **Human-in-the-Loop Command Center:** A modern dark-mode Streamlit dashboard allows marketing managers to review, approve, or reject posts with one click.
* **Offline Demo Resilience:** Pre-cached fallback snapshot guarantees 100% uptime during presentations or API outages.

---

## 🏗️ System Architecture & Workflow

```
       [ SQLite Database ] ── (Sales, Stock, Margins, Events)
               │
               ▼
   ┌─────────────────────────────────────────────────────────┐
   │            CrewAI Multi-Agent Pipeline                  │
   │                                                         │
   │  [Sales Analyst] ──► [Strategist] ──► [Copywriter]     │
   │                                            │            │
   │                                            ▼            │
   │                                  [Scheduling Agent]     │
   └───────────────────────────┬─────────────────────────────┘
                               │
                               ▼
   ┌─────────────────────────────────────────────────────────┐
   │       Application-Level Safety Gates (Python/DB)        │
   │                                                         │
   │   🛡️ Stock Guard    🛡️ Fake Claims    🛡️ Posting Cap    │
   │   (Stock >= 20)     (Fact-Checked)   (<= 5 posts/day)  │
   └───────────────────────────┬─────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       [ Post Approval Queue ]        [ Cached Fallback JSON ]
       (Pending / Approved / Rejected) (Offline / Demo Mode)
               │                               │
               └───────────────┬───────────────┘
                               ▼
                   [ Streamlit Command Center ]
                   (Review, Approve, Analytics)
```

### End-to-End Execution Flow (5 Steps):
1. **Data Ingestion:** User triggers the campaign. The **Sales Analyst** queries live order revenue, velocity, stock levels, and margin data.
2. **Strategic Alignment:** The **Campaign Strategist** selects high-margin, in-stock products and pairs them with upcoming calendar events.
3. **Bilingual Copy Creation:** The **Copywriter** crafts high-converting copy in **English**, **Roman Urdu**, and **WhatsApp Broadcast** formats.
4. **Safety Interception:** The **Scheduling Coordinator** calls `save_post_to_queue`, triggering three hard validation gates:
   - **Stock Guard:** Rejects products below defined stock threshold.
   - **Fake Claims Guard:** Rejects invented discounts, wrong prices, and unbacked scarcity.
   - **Posting Cap:** Enforces daily post limits and suggests the next open date.
5. **Human Review:** Safe posts land in the approval queue. The marketing manager clicks **✅ Approve** or **❌ Reject**.

---

## 🤖 The 4 Specialized Agents

| Agent | Role | Goal |
|---|---|---|
| **📊 Sales Analyst** | Senior E-commerce Retail Analyst | Identify top-selling, high-margin, and trending products from database facts. |
| **🎯 Campaign Strategist** | Digital Marketing Strategist | Match winning products with upcoming events, peak days, and audience segments. |
| **✍️ Creative Copywriter** | Bilingual E-Commerce Copywriter | Craft persuasive, culturally resonant copy in English and authentic Roman Urdu. |
| **📅 Scheduling Coordinator** | Social Media Campaign Scheduler | Determine optimal posting schedule, check safety limits, and populate the queue. |

---

## 🛡️ Enterprise Safety & Reliability Gates

Safety in MarketMate is **deterministic Python and SQL validation**, never relying purely on LLM prompt instructions:

* **🛡️ Stock Guard (`STOCK_THRESHOLD = 20`):**
  Live database check. Blocks posts for products with stock below threshold (e.g. *White Shalwar* with 15 units is automatically blocked).
* **🔍 Fake Claims Guard:**
  Regex fact-checker scans copy for:
  - Invented percentage discounts (`"20% off"`).
  - Fabricated stock scarcity (`"only 3 left"`).
  - Invented prices differing from database records.
* **⏱️ Posting Cap (`MAX_POSTS_PER_DAY = 5`):**
  Prevents audience fatigue by rejecting excess daily posts and automatically finding the next available date.
* **🔄 Fault Tolerance & Cached Fallback:**
  - Automatic retry once on transient API failures.
  - Cached JSON snapshot (`data/fallback_result.json`) allows running complete offline demonstrations without incurring API costs.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **AI Multi-Agent Framework** | **CrewAI (v1.15+)** | Agent delegation, sequential workflows, tool execution |
| **Foundation LLM** | **Google Gemini 3.5 Flash** | Sub-second inference, reasoning, and bilingual fluency |
| **User Interface** | **Streamlit (v1.64+)** | Interactive dashboard with real-time stats and approvals |
| **Database** | **SQLite3** | Zero-latency local relational storage |
| **Validation Engine** | **Python (Regex + Custom Exceptions)** | Deterministic stock, claim, and rate limiting enforcement |
| **Styling & Design System** | **Custom CSS & Plus Jakarta Sans** | Modern high-contrast dark theme with status badges |

---

## 📁 Project Structure

```
MarketMate/
├── .streamlit/
│   └── config.toml          # Dark theme configuration
├── data/
│   ├── marketmate.db        # SQLite database (products, orders, events, queue)
│   ├── generate_data.py     # Database seeding and reset script
│   └── fallback_result.json # Verified offline demo snapshot
├── tools/
│   ├── market_tools.py      # Database access tools & Safety Gates
│   └── safety.py            # Language quality checker & fallback manager
├── agents.py                # 4 CrewAI agent definitions
├── tasks.py                 # Sequential task specifications
├── crew.py                  # Pipeline entry point with retry & fallback
├── app.py                   # Streamlit dashboard & approval queue UI
├── requirements.txt         # Pinned production dependencies
├── .python-version          # Python 3.11 pin for cloud deployment
├── runtime.txt              # Cloud runtime declaration
├── .env.example             # Template for API credentials
└── README.md                # Project documentation
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.11 or 3.12
- Google Gemini API key ([Get one from Google AI Studio](https://aistudio.google.com/apikey))

### 2. Clone and Setup Environment

```powershell
# Clone the repository
git clone https://github.com/your-username/MarketMate.git
cd MarketMate

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # On Windows
# source .venv/bin/activate     # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Credentials

Copy the environment template and insert your Gemini API key:

```powershell
Copy-Item .env.example .env     # On Windows
# cp .env.example .env          # On macOS/Linux
```

Inside `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
MODEL=gemini/gemini-3.5-flash
CREWAI_TELEMETRY_OPT_OUT=true
OTEL_SDK_DISABLED=true
```

### 4. Seed Database (Optional)
A pre-seeded database is already included, but you can re-generate mock retail data at any time:
```powershell
python data/generate_data.py
```

### 5. Launch the Dashboard
```powershell
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## ☁️ Deployment on Streamlit Community Cloud

1. Push your repository to **GitHub**.
2. Sign in to **[share.streamlit.io](https://share.streamlit.io)** with GitHub.
3. Click **"New App"**, select your repository, branch `main`, and main file `app.py`.
4. Under **"Advanced settings..."** &rarr; **"Secrets"**, add:
   ```toml
   GEMINI_API_KEY = "your_gemini_api_key"
   MODEL = "gemini/gemini-3.5-flash"
   CREWAI_TELEMETRY_OPT_OUT = "true"
   OTEL_SDK_DISABLED = "true"
   ```
5. Ensure Python version is set to **3.11** (handled automatically via `.python-version`).
6. Click **Deploy!**

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
