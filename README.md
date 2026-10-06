# 🏛️ US Federal AI Policy Tracker

A Streamlit web application that uses live web search to track and summarize current US federal AI policy developments, aligned with the NIST AI Risk Management Framework (AI RMF).

## Overview

Staying current on the AI regulatory landscape is a core responsibility in AI governance. This tool automatically fetches and organizes the latest US federal AI policy activity (executive orders, legislation, and agency guidance) into a structured, filterable dashboard with downloadable governance reports.

## Features

- **Live web search** powered by Claude and the Anthropic Web Search API
- **Three policy categories tracked**:
  - 🔴 Executive Orders: Presidential directives on AI
  - 🟢 Legislation: Bills and acts in Congress
  - 🟣 Agency Guidance: NIST, FTC, FDA, DOD, OMB, and others
- **Significance ratings** (High / Medium / Low) for prioritization
- **Status tracking** (Active, Proposed, Passed, Pending, Revoked)
- **Filter by type, status, and significance**
- **Summary dashboard** with charts and data table
- **Downloadable governance report** aligned with NIST AI RMF GOVERN function

## Motivation

AI governance practitioners must maintain awareness of the regulatory environment in which AI systems operate. NIST AI RMF subcategory GV-1.1 calls for legal and regulatory requirements involving AI to be understood, managed, and documented. This tool supports that outcome for US federal policy.

## Getting Started

### Prerequisites
- Python 3.9+
- Anthropic API key ([get one here](https://console.anthropic.com))

### Installation

```bash
git clone https://github.com/srhill12/ai-policy-tracker.git
cd ai-policy-tracker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Copy the example env file and add your API key:

```bash
cp .env.example .env
```

Edit `.env`:
```
ANTHROPIC_API_KEY=your-api-key-here
```

### Running the App

```bash
python -m streamlit run app.py
```

## Usage

1. Click **Fetch Latest Updates** in the sidebar
2. Wait about 15 to 20 seconds while Claude searches the web for current policy developments
3. Browse the **Policy Feed** tab for individual items
4. Check the **Summary View** tab for charts and the full data table
5. Download a formal **Governance Report** from the Report tab

## NIST AI RMF Alignment

| Function | Sub-category | How this tool helps |
|----------|-------------|---------------------|
| GOVERN | GV-1.1 | Surfaces US federal legal and regulatory developments involving AI so they can be understood and documented |

## Project Structure

```
ai-policy-tracker/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Excludes .env and venv
└── README.md           # This file
```

## Author

Steven Hill | AI Governance Professional | AIGP | ISO/IEC 42001 Lead Auditor

[LinkedIn](https://linkedin.com/in/stevenrhill) | [GitHub](https://github.com/srhill12)

## References

- NIST (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*, NIST AI 100-1. https://doi.org/10.6028/NIST.AI.100-1

### Current

- Executive Order 14179, *Removing Barriers to American Leadership in Artificial Intelligence* (January 23, 2025). https://www.federalregister.gov/documents/2025/01/31/2025-02172/removing-barriers-to-american-leadership-in-artificial-intelligence
- OMB Memorandum M-25-21, *Accelerating Federal Use of AI through Innovation, Governance, and Public Trust* (April 3, 2025). https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf
- OMB Memorandum M-26-04, *Increasing Public Trust in Artificial Intelligence Through Unbiased AI Principles* (December 11, 2025). Implements the Unbiased AI Principles of Executive Order 14319, *Preventing Woke AI in the Federal Government* (July 23, 2025), for federal procurement of large language models. https://www.whitehouse.gov/wp-content/uploads/2025/12/M-26-04-Increasing-Public-Trust-in-Artificial-Intelligence-Through-Unbiased-AI-Principles-1.pdf

### Historical Context (No Longer in Effect)

These instruments shaped earlier federal AI policy and may still appear in search results, but they are not current:

- Executive Order 14110, *Safe, Secure, and Trustworthy Development and Use of Artificial Intelligence* (October 30, 2023). Revoked on January 20, 2025 by Executive Order 14148, *Initial Rescissions of Harmful Executive Orders and Actions*. https://www.federalregister.gov/documents/2025/01/28/2025-01901/initial-rescissions-of-harmful-executive-orders-and-actions
- OMB Memorandum M-24-10, *Advancing Governance, Innovation, and Risk Management for Agency Use of Artificial Intelligence* (March 2024). Rescinded and replaced on April 3, 2025 by OMB Memorandum M-25-21, *Accelerating Federal Use of AI through Innovation, Governance, and Public Trust*. https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf
