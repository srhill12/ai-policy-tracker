import streamlit as st
import html
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import anthropic

from grounding import UNVERIFIED, VERIFIED, collect_search_results, ground_items

load_dotenv()

POLICY_TYPES = ["Executive Order", "Legislation", "Agency Guidance"]
STATUSES = ["Active", "Proposed", "Passed", "Pending", "Revoked"]
SIGNIFICANCE_LEVELS = ["High", "Medium", "Low"]

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="US Federal AI Policy Tracker",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .policy-card {
        background: white;
        border-radius: 10px;
        padding: 20px 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        margin-bottom: 16px;
        border-left: 5px solid #2E4057;
    }
    .policy-card.legislation { border-left-color: #1a6b3c; }
    .policy-card.guidance    { border-left-color: #7b4ea6; }
    .policy-card.executive   { border-left-color: #c0392b; }
    .policy-card.other       { border-left-color: #888; }
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78em;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-eo   { background:#fde8e8; color:#c0392b; }
    .badge-leg  { background:#e8f5ee; color:#1a6b3c; }
    .badge-guid { background:#f0e8f7; color:#7b4ea6; }
    .badge-oth  { background:#f0f0f0; color:#555; }
    .badge-high   { background:#fde8e8; color:#c0392b; }
    .badge-medium { background:#fff3cd; color:#856404; }
    .badge-low    { background:#e8f5ee; color:#1a6b3c; }
    .badge-active   { background:#e8f5ee; color:#1a6b3c; }
    .badge-proposed { background:#fff3cd; color:#856404; }
    .badge-revoked  { background:#f0f0f0; color:#555; }
    .badge-passed   { background:#e8f0fe; color:#1a56a6; }
    .badge-pending  { background:#fff3cd; color:#856404; }
    .badge-unverified { background:#fff3cd; color:#7a4b00; border:1px solid #e0a800; }
    .badge-primary    { background:#e8f0fe; color:#1a56a6; }
    .badge-secondary  { background:#f0f0f0; color:#555; }
    .source-list { color: #444; font-size: 0.82em; margin-top: 8px; }
    .source-list a { color: #1a56a6; }
    .rejected-note { color: #a04000; font-size: 0.78em; margin-top: 6px; }
    .summary-text { color: #444; font-size: 0.93em; line-height: 1.6; margin-top: 10px; }
    .meta-text { color: #888; font-size: 0.82em; margin-top: 6px; }
    .report-box {
        background: white;
        color: #1a1a1a !important;
        border-left: 5px solid #2E4057;
        padding: 20px 24px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 0.85em;
        line-height: 1.7;
        white-space: pre-wrap;
    }
    .report-box * { color: #1a1a1a !important; }
</style>
""", unsafe_allow_html=True)

# ── API key handling ──────────────────────────────────────────────────────────
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    st.error("⚠️ ANTHROPIC_API_KEY not found. Please add it to your .env file.")
    st.code("ANTHROPIC_API_KEY=your-key-here", language="bash")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# ── Fetch policy data ─────────────────────────────────────────────────────────
MAX_PAUSE_CONTINUATIONS = 3

def fetch_policy_data():
    prompt = f"""Search the web for the most current and significant US federal AI policy developments.

Find 12-16 items across these categories:
- Executive Orders related to AI (including any recent ones signed or revoked)
- Federal legislation related to AI (passed or pending in Congress)  
- Agency guidance on AI (from NIST, FTC, EEOC, FDA, DOD, OMB, DHS, or other agencies)

For each item return a JSON object. Respond ONLY with a valid JSON array: no markdown, no backticks, no preamble.

Each object must have exactly these fields:
{{
  "title": "official title of the order, bill, or guidance document",
  "type": one of {json.dumps(POLICY_TYPES)},
  "date": "YYYY-MM-DD or YYYY-MM if exact date unknown",
  "status": one of {json.dumps(STATUSES)},
  "agency": "issuing agency or department name",
  "summary": "2-3 sentence plain English summary of what it does and why it matters for AI governance",
  "significance": one of {json.dumps(SIGNIFICANCE_LEVELS)},
  "source_urls": ["1 to 3 URLs from your web search results that support this item"]
}}

Use "Revoked" for items that have been revoked, rescinded, repealed, or superseded and are no longer in effect.

Rules for source_urls:
- Copy each URL exactly, character for character, from a web search result you retrieved in this conversation.
- Never construct, guess, shorten, or edit a URL. URLs not found in the search results will be discarded.
- Prefer official government sources (.gov) when the search results include them.
- If no search result supports an item, use an empty list.

Prioritize accuracy and recency. Include the most impactful items first."""

    messages = [{"role": "user", "content": prompt}]
    content_blocks = []
    for _ in range(MAX_PAUSE_CONTINUATIONS + 1):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=8000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=messages
        )
        content_blocks.extend(response.content)
        if response.stop_reason != "pause_turn":
            break
        messages = [messages[0], {"role": "assistant", "content": content_blocks}]

    # Extract all text content from response blocks
    full_text = ""
    for block in content_blocks:
        if getattr(block, "type", None) == "text" and block.text:
            full_text += block.text

    full_text = full_text.strip()

    # Find the JSON array - look for [ ... ] anywhere in the response
    start = full_text.find("[")
    end = full_text.rfind("]")

    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in response. Response was:\n{full_text[:500]}")

    json_str = full_text[start:end+1]
    items = json.loads(json_str)
    return ground_items(items, collect_search_results(content_blocks))

# ── Helper: badge HTML ────────────────────────────────────────────────────────
def type_badge(t):
    cls = {"Executive Order": "badge-eo", "Legislation": "badge-leg",
           "Agency Guidance": "badge-guid"}.get(t, "badge-oth")
    return f'<span class="badge {cls}">{html.escape(str(t))}</span>'

def sig_badge(s):
    cls = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(s, "badge-oth")
    return f'<span class="badge {cls}">⬤ {html.escape(str(s))} Significance</span>'

def status_badge(s):
    cls = {"Active": "badge-active", "Proposed": "badge-proposed", "Revoked": "badge-revoked",
           "Passed": "badge-passed", "Pending": "badge-pending"}.get(s, "badge-oth")
    return f'<span class="badge {cls}">{html.escape(str(s))}</span>'

def source_badge(item):
    if item.get("verification") != VERIFIED:
        return f'<span class="badge badge-unverified">⚠ {UNVERIFIED}: no source from search results</span>'
    if item.get("source_type") == "primary":
        return '<span class="badge badge-primary">Primary source</span>'
    return '<span class="badge badge-secondary">Secondary source</span>'

def card_class(t):
    return {"Executive Order": "executive", "Legislation": "legislation",
            "Agency Guidance": "guidance"}.get(t, "other")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏛️ AI Policy Tracker")
    st.markdown("**Scope:** US Federal AI Policy  \n**Source:** Live web search via Claude")
    st.markdown("---")

    if st.button("🔄 Fetch Latest Updates", type="primary", use_container_width=True):
        with st.spinner("Searching for latest US federal AI policy developments..."):
            try:
                st.session_state["policy_data"] = fetch_policy_data()
                st.session_state["fetch_time"] = datetime.now().strftime("%B %d, %Y at %I:%M %p")
                st.success("Data updated!")
            except Exception as e:
                st.error(f"Fetch failed: {e}")

    st.markdown("---")
    st.markdown("### 🔍 Filters")

    filter_type = st.multiselect(
        "Policy Type",
        POLICY_TYPES,
        default=POLICY_TYPES
    )

    filter_status = st.multiselect(
        "Status",
        STATUSES,
        default=STATUSES
    )

    filter_sig = st.multiselect(
        "Significance",
        SIGNIFICANCE_LEVELS,
        default=SIGNIFICANCE_LEVELS
    )

    st.markdown("---")
    st.caption("Built to demonstrate applied AI governance and regulatory landscape awareness. Powered by Claude + live web search.")

# ── Main content ──────────────────────────────────────────────────────────────
st.markdown("# 🏛️ US Federal AI Policy Tracker")
st.markdown("Real-time tracking of executive orders, legislation, and agency guidance shaping AI governance in the United States.")
st.markdown("---")

# ── No data yet ───────────────────────────────────────────────────────────────
if "policy_data" not in st.session_state:
    st.info("👈 Click **Fetch Latest Updates** in the sidebar to load current AI policy data.")
    st.markdown("""
    **What this tool tracks:**
    - 🔴 **Executive Orders**: Presidential directives on AI development, safety, and use
    - 🟢 **Legislation**: Bills and acts passed or pending in Congress
    - 🟣 **Agency Guidance**: Policy documents from NIST, FTC, FDA, DOD, OMB, and others
    
    **Aligned with:** NIST AI RMF GOVERN function, maintaining awareness of the regulatory environment in which AI systems operate.
    """)
    st.stop()

# ── Filter data ───────────────────────────────────────────────────────────────
data = st.session_state["policy_data"]
fetch_time = st.session_state.get("fetch_time", "Unknown")

filtered = [
    item for item in data
    if item.get("type") in filter_type
    and item.get("status") in filter_status
    and item.get("significance") in filter_sig
]

# ── Summary metrics ───────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Items", len(data))
col2.metric("Showing", len(filtered))
col3.metric("High Significance", sum(1 for i in data if i.get("significance") == "High"))
col4.metric("Active / Passed", sum(1 for i in data if i.get("status") in ["Active", "Passed"]))
col5.metric("Last Updated", fetch_time.split(" at ")[0] if fetch_time else "N/A")

st.markdown(f"*Last fetched: {fetch_time}*")
st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Policy Feed", "📊 Summary View", "📄 Governance Report"])

# ════════════════════════════════════════════════════════
# TAB 1: POLICY FEED
# ════════════════════════════════════════════════════════
with tab1:
    if not filtered:
        st.warning("No items match the current filters.")
    else:
        # Sort by significance then date
        sig_order = {"High": 0, "Medium": 1, "Low": 2}
        sorted_items = sorted(filtered, key=lambda x: (sig_order.get(x.get("significance", "Low"), 2), x.get("date", "")), reverse=False)
        sorted_items = sorted(sorted_items, key=lambda x: sig_order.get(x.get("significance", "Low"), 2))

        title_style = "font-size:1.05em;font-weight:700;color:#2E4057;text-decoration:none;"
        for item in sorted_items:
            t = item.get("type", "Other")
            cc = card_class(t)
            title = html.escape(str(item.get("title", "Untitled")))
            agency = html.escape(str(item.get("agency", "Unknown Agency")))
            date = html.escape(str(item.get("date", "Date unknown")))
            summary = html.escape(str(item.get("summary", "")))
            status = item.get("status", "Unknown")
            sig = item.get("significance", "Medium")
            sources = item.get("sources", [])
            rejected = item.get("rejected_urls", [])

            if sources:
                href = html.escape(sources[0]["url"], quote=True)
                title_html = f'<a href="{href}" target="_blank" style="{title_style}">{title} ↗</a>'
                links = " &nbsp;|&nbsp; ".join(
                    f'<a href="{html.escape(s["url"], quote=True)}" target="_blank">'
                    f'{html.escape(s.get("title") or s["url"])}</a> ({s["source_type"]})'
                    for s in sources
                )
                sources_html = f'<div class="source-list">Sources: {links}</div>'
            else:
                title_html = f'<span style="{title_style}">{title}</span>'
                sources_html = ""

            rejected_html = ""
            if rejected:
                rejected_html = (
                    f'<div class="rejected-note">{len(rejected)} model-supplied URL(s) discarded '
                    f'because they did not appear in the search results.</div>'
                )

            st.markdown(
                f'<div class="policy-card {cc}">'
                f'<div>{type_badge(t)} {status_badge(status)} {sig_badge(sig)} {source_badge(item)}</div>'
                f'<div style="margin-top:10px">{title_html}</div>'
                f'<div class="meta-text">🏛️ {agency} &nbsp;|&nbsp; 📅 {date}</div>'
                f'<div class="summary-text">{summary}</div>'
                f'{sources_html}{rejected_html}'
                f'</div>',
                unsafe_allow_html=True
            )

# ════════════════════════════════════════════════════════
# TAB 2: SUMMARY VIEW
# ════════════════════════════════════════════════════════
with tab2:
    import plotly.express as px
    import pandas as pd

    df = pd.DataFrame(data)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Items by Type")
        type_counts = df["type"].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        colors = {"Executive Order": "#c0392b", "Legislation": "#1a6b3c", "Agency Guidance": "#7b4ea6"}
        fig1 = px.bar(type_counts, x="Type", y="Count",
                      color="Type",
                      color_discrete_map=colors,
                      text="Count")
        fig1.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                           showlegend=False, margin=dict(t=20, b=20), height=300)
        fig1.update_traces(textposition="outside")
        st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        st.markdown("#### Items by Significance")
        sig_counts = df["significance"].value_counts().reset_index()
        sig_counts.columns = ["Significance", "Count"]
        sig_colors = {"High": "#c0392b", "Medium": "#f39c12", "Low": "#1a6b3c"}
        fig2 = px.pie(sig_counts, names="Significance", values="Count",
                      color="Significance",
                      color_discrete_map=sig_colors,
                      hole=0.4)
        fig2.update_layout(paper_bgcolor="white", margin=dict(t=20, b=20), height=300)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Status Breakdown")
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    fig3 = px.bar(status_counts, x="Count", y="Status", orientation="h",
                  color_discrete_sequence=["#2E4057"],
                  text="Count")
    fig3.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                       margin=dict(t=20, b=20), height=280)
    fig3.update_traces(textposition="outside")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### Full Data Table")
    display_df = df[["title", "type", "date", "status", "agency", "significance",
                     "verification", "source_type"]].copy()
    display_df["source_type"] = display_df["source_type"].fillna("N/A")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════
# TAB 3: GOVERNANCE REPORT
# ════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Regulatory Landscape Report")
    st.markdown("Structured summary of current US federal AI policy activity, aligned with NIST AI RMF GOVERN function.")

    report_items = [i for i in data if i.get("verification") == VERIFIED]
    excluded_count = len(data) - len(report_items)
    if excluded_count:
        st.info(f"{excluded_count} {UNVERIFIED.lower()} item(s) excluded from this report because "
                f"no source URL from the web search results supports them.")

    now = datetime.now().strftime("%B %d, %Y")
    high_items = [i for i in report_items if i.get("significance") == "High"]
    active_items = [i for i in report_items if i.get("status") in ["Active", "Passed"]]
    eo_items = [i for i in report_items if i.get("type") == "Executive Order"]
    leg_items = [i for i in report_items if i.get("type") == "Legislation"]
    guid_items = [i for i in report_items if i.get("type") == "Agency Guidance"]

    report = f"""
US FEDERAL AI POLICY LANDSCAPE REPORT
{'='*60}
Generated:     {now}
Data Source:   Live web search (Claude + Anthropic Web Search API)
Scope:         US Federal AI Policy (Executive, Legislative, Regulatory)
NIST AI RMF:   GOVERN Function, Regulatory Awareness

OVERVIEW
─────────────────────────────────────────────────────────
Verified items in report:      {len(report_items)}
Unverified items excluded:     {excluded_count}
High significance items:       {len(high_items)}
Active or passed items:        {len(active_items)}
Executive Orders:              {len(eo_items)}
Legislation:                   {len(leg_items)}
Agency Guidance:               {len(guid_items)}

HIGH SIGNIFICANCE ITEMS
─────────────────────────────────────────────────────────
"""
    for item in high_items:
        source_lines = "\n".join(
            f"  Source:  {s['url']} ({s['source_type']})" for s in item.get("sources", [])
        )
        report += f"""
► {item.get('title', 'Unknown')}
  Type:    {item.get('type', 'N/A')}
  Agency:  {item.get('agency', 'N/A')}
  Date:    {item.get('date', 'N/A')}
  Status:  {item.get('status', 'N/A')}
  Summary: {item.get('summary', 'N/A')}
{source_lines}
"""

    report += f"""
EXECUTIVE ORDERS
─────────────────────────────────────────────────────────
"""
    for item in eo_items:
        report += f"  [{item.get('status','?')}] {item.get('title','?')} ({item.get('date','?')})\n"

    report += f"""
LEGISLATION
─────────────────────────────────────────────────────────
"""
    for item in leg_items:
        report += f"  [{item.get('status','?')}] {item.get('title','?')} ({item.get('date','?')})\n"

    report += f"""
AGENCY GUIDANCE
─────────────────────────────────────────────────────────
"""
    for item in guid_items:
        report += f"  [{item.get('status','?')}] {item.get('agency','?')}: {item.get('title','?')} ({item.get('date','?')})\n"

    report += f"""
NIST AI RMF ALIGNMENT NOTE
─────────────────────────────────────────────────────────
This report supports the GOVERN function of the NIST AI RMF,
specifically GV-1.1 (legal and regulatory requirements
involving AI are understood, managed, and documented).

Organizations deploying AI systems should review high
significance items and assess applicability to their
specific use cases and deployment contexts.

SOURCE GROUNDING
─────────────────────────────────────────────────────────
Only items supported by at least one URL returned by the
web search tool are included. Primary sources are .gov or
.mil sites; all others are secondary.

DISCLAIMER
─────────────────────────────────────────────────────────
This report is generated from live web search results and
is intended for informational purposes only. It does not
constitute legal advice. Always verify regulatory
requirements with qualified legal counsel.
{'='*60}
"""

    st.markdown(f'<div class="report-box">{html.escape(report, quote=False)}</div>', unsafe_allow_html=True)

    st.download_button(
        label="⬇️ Download Report (.txt)",
        data=report,
        file_name=f"ai_policy_report_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )
