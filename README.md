# 🏛️ US Federal AI Policy Tracker

A Streamlit web application that uses live web search to track and summarize current US federal AI policy developments, aligned with the NIST AI Risk Management Framework (AI RMF).

## Overview

Staying current on the AI regulatory landscape is a core responsibility in AI governance. This tool automatically fetches and organizes the latest US federal AI policy activity — executive orders, legislation, and agency guidance — into a structured, filterable dashboard with downloadable governance reports.

## Features

- **Live web search** powered by Claude and the Anthropic Web Search API
- **Three policy categories tracked**:
  - 🔴 Executive Orders — Presidential directives on AI
  - 🟢 Legislation — Bills and acts in Congress
  - 🟣 Agency Guidance — NIST, FTC, FDA, DOD, OMB, and others
- **Significance ratings** (High / Medium / Low) for prioritization
- **Status tracking** (Active, Proposed, Passed, Pending, Revoked)
- **Filter by type, status, and significance**
- **Summary dashboard** with charts and data table
- **Downloadable governance report** aligned with NIST AI RMF GOVERN function

## Motivation

AI governance practitioners must maintain awareness of the regulatory environment in which AI systems operate. The NIST AI RMF GOVERN function (GV-1.1, GV-6.1) specifically requires organizations to identify and track applicable laws and regulations. This tool operationalizes that requirement.

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
2. Wait ~15–20 seconds while Claude searches the web for current policy developments
3. Browse the **Policy Feed** tab for individual items
4. Check the **Summary View** tab for charts and the full data table
5. Download a formal **Governance Report** from the Report tab

## NIST AI RMF Alignment

| Function | Sub-category | How this tool helps |
|----------|-------------|---------------------|
| GOVERN | GV-1.1 | Identifies applicable laws and regulations |
| GOVERN | GV-6.1 | Tracks regulatory requirements over time |
| MAP | MP-2.3 | Contextualizes regulatory risk for AI deployments |

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

Steven Hill — Purdue University MSAI Candidate | AI Governance, Responsible AI & Adoption Enablement

[LinkedIn](https://linkedin.com/in/stevenrhill) | [GitHub](https://github.com/srhill12)

## References

- NIST (2023). *AI Risk Management Framework (AI RMF 1.0)*
- Executive Order 14110 on Safe, Secure, and Trustworthy AI (2023)
- OMB Memorandum M-24-10 on AI Governance (2024)
