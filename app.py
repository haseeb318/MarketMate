"""
MarketMate – app.py
Streamlit front-end for AI E-commerce Marketing with Safety Gates.

UI Design System
────────────────
- High-contrast, solid dark surface design (#0B0F19 background, #151D2F cards)
- Typography: Plus Jakarta Sans with crystal-clear text contrast across all sections
- Color Accents: Electric Indigo (#6366F1), Emerald (#10B981), Amber (#F59E0B), Crimson (#EF4444)
- Styled sidebar with solid safety cards, demo fallback control, and system status
- Hero banner with high-contrast workflow indicators
- Tabbed campaign result viewer (Plan vs Quality Advisory)
- Approval queue with live stat counters, high-visibility badges, and solid card layout
"""
from __future__ import annotations

import os

os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st

from crew import LLMFailedError, main
from tools.market_tools import (
    MAX_POSTS_PER_DAY,
    STOCK_THRESHOLD,
    get_post_queue,
    update_post_status,
)
from tools.safety import load_fallback, review_campaign_content

# ─── Page Configuration ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="MarketMate | AI Marketing Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── High-Contrast Typography & CSS Design System ────────────────────────────

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #F1F5F9;
    }
    
    /* Ensure native markdown headers and text are bright and legible */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }
    p, span, label, div {
        color: #E2E8F0;
    }
    
    /* Hero Banner - Solid high-contrast container */
    .mm-hero {
        background: #131B2E;
        border: 1px solid #312E81;
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    }
    .mm-hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #FFFFFF !important;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }
    .mm-hero-sub {
        color: #CBD5E1 !important;
        font-size: 1.02rem;
        line-height: 1.55;
        margin-bottom: 16px;
    }
    .mm-workflow-steps {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 10px;
    }
    .mm-step-pill {
        background: #1E293B;
        border: 1px solid #4338CA;
        border-radius: 9999px;
        padding: 6px 14px;
        font-size: 0.82rem;
        color: #E0E7FF !important;
        font-weight: 600;
    }

    /* Sidebar Solid Cards */
    .sidebar-card {
        background: #151D2F;
        border: 1px solid #26334D;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 14px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    .sidebar-card-title {
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8 !important;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .sidebar-card-value {
        font-size: 1.45rem;
        font-weight: 800;
        color: #FFFFFF !important;
    }
    .sidebar-card-sub {
        font-size: 0.78rem;
        color: #94A3B8 !important;
        margin-top: 4px;
        line-height: 1.4;
    }
    
    /* Stat Bar Cards */
    .stat-box {
        background: #151D2F;
        border: 1px solid #26334D;
        border-radius: 12px;
        padding: 14px 16px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    .stat-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #CBD5E1 !important;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .stat-num {
        font-size: 1.8rem;
        font-weight: 800;
        color: #FFFFFF !important;
    }

    /* Post Queue Card - Solid high-contrast container */
    .post-card {
        background: #151D2F;
        border: 1px solid #26334D;
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.25);
        transition: border-color 0.2s ease, transform 0.2s ease;
    }
    .post-card:hover {
        border-color: #6366F1;
    }
    
    /* Badges & Chips - Solid opaque backgrounds for 100% legibility */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .badge-pending {
        background: #78350F;
        color: #FDE68A !important;
        border: 1px solid #D97706;
    }
    .badge-approved {
        background: #064E3B;
        color: #A7F3D0 !important;
        border: 1px solid #059669;
    }
    .badge-rejected {
        background: #7F1D1D;
        color: #FECACA !important;
        border: 1px solid #DC2626;
    }
    .badge-platform {
        background: #312E81;
        color: #E0E7FF !important;
        border: 1px solid #4F46E5;
    }
    .badge-time {
        background: #1E293B;
        color: #E2E8F0 !important;
        border: 1px solid #334155;
    }

    /* Post Content Box - Deep rich solid background with crystal-clear white text */
    .post-content-box {
        background: #0B0F19;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 16px 18px;
        margin-top: 14px;
        margin-bottom: 14px;
        color: #F8FAFC !important;
        font-size: 0.98rem;
        line-height: 1.65;
        white-space: pre-wrap;
        box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.35);
    }

    /* Demo / Cache Banner - Solid Amber */
    .demo-banner {
        background: #451A03;
        border: 1px solid #D97706;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 20px;
        color: #FEF3C7 !important;
        font-size: 0.95rem;
        line-height: 1.5;
        box-shadow: 0 4px 14px rgba(217, 119, 6, 0.15);
    }
    
    /* Success Banner - Solid Emerald */
    .success-banner {
        background: #064E3B;
        border: 1px solid #059669;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 20px;
        color: #D1FAE5 !important;
        font-size: 0.95rem;
        line-height: 1.5;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.15);
    }

    /* Buttons */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
        color: #FFFFFF !important;
        border: 1px solid #818CF8;
        border-radius: 10px;
        font-weight: 700;
        font-size: 0.98rem;
        padding: 10px 24px;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3);
        transition: all 0.2s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        transform: translateY(-1px);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 4px 0 18px 0; border-bottom: 1px solid #26334D; margin-bottom: 16px;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #FFFFFF; display: flex; align-items: center; gap: 8px;">
                <span style="color: #6366F1;">⚡</span> MarketMate
            </div>
            <div style="font-size: 0.8rem; color: #818CF8; font-weight: 700; letter-spacing: 0.04em; margin-top: 2px;">
                PAKISTAN RETAIL AI STUDIO
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🛡️ Safety & Reliability")

    # Stock Guard Card
    st.markdown(
        f"""
        <div class="sidebar-card">
            <div class="sidebar-card-title">Stock Threshold</div>
            <div class="sidebar-card-value">{STOCK_THRESHOLD} units</div>
            <div class="sidebar-card-sub">Posts blocked below this inventory level</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Posting Cap Card
    st.markdown(
        f"""
        <div class="sidebar-card">
            <div class="sidebar-card-title">Daily Posting Cap</div>
            <div class="sidebar-card-value">{MAX_POSTS_PER_DAY} posts / day</div>
            <div class="sidebar-card-sub">Prevents social media spam & overscheduling</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Offline / Demo Mode Card
    st.markdown("### 🗂️ Demo Snapshot")
    cached = load_fallback()
    if cached:
        saved_date = cached.get("saved_at", "recently")
        st.markdown(
            f"""
            <div class="sidebar-card" style="border-color: #059669;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <span style="height: 10px; width: 10px; background: #10B981; border-radius: 50%; display: inline-block;"></span>
                    <span style="font-size: 0.84rem; font-weight: 700; color: #34D399;">Snapshot Available</span>
                </div>
                <div class="sidebar-card-sub">Saved on <strong>{saved_date}</strong> (Zero API Cost)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("📥 Load Cached Result", key="load_cache_btn", use_container_width=True):
            quality_issues = review_campaign_content(cached["result"])
            st.session_state["campaign_data"] = {
                "result": cached["result"],
                "from_cache": True,
                "cached_at": cached.get("saved_at"),
                "quality_issues": quality_issues,
            }
            st.rerun()
    else:
        st.info("Run the live campaign once to create an offline demo snapshot.")

    st.markdown("---")

    # System Status Panel
    active_model = os.getenv("MODEL", "gemini/gemini-3.5-flash").replace("gemini/", "")
    st.markdown(
        f"""
        <div class="sidebar-card" style="font-size: 0.82rem;">
            <div class="sidebar-card-title">System Status</div>
            <div style="margin-top: 8px; display: flex; justify-content: space-between; border-bottom: 1px solid #1E293B; padding-bottom: 4px;">
                <span style="color: #94A3B8;">AI Model:</span> <strong style="color: #FFFFFF;">{active_model}</strong>
            </div>
            <div style="margin-top: 6px; display: flex; justify-content: space-between; border-bottom: 1px solid #1E293B; padding-bottom: 4px;">
                <span style="color: #94A3B8;">Engine:</span> <strong style="color: #FFFFFF;">CrewAI v0.102</strong>
            </div>
            <div style="margin-top: 6px; display: flex; justify-content: space-between; border-bottom: 1px solid #1E293B; padding-bottom: 4px;">
                <span style="color: #94A3B8;">Telemetry:</span> <strong style="color: #34D399;">Opted Out</strong>
            </div>
            <div style="margin-top: 6px; display: flex; justify-content: space-between;">
                <span style="color: #94A3B8;">Database:</span> <strong style="color: #34D399;">SQLite Active</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─── Main Content ─────────────────────────────────────────────────────────────

# Hero Header
st.markdown(
    """
    <div class="mm-hero">
        <div class="mm-hero-title">⚡ E-Commerce Marketing Command Center</div>
        <div class="mm-hero-sub">
            Autonomous multi-agent marketing campaign orchestrator powered by live inventory, profit margins, and sales trends.
        </div>
        <div class="mm-workflow-steps">
            <span class="mm-step-pill">📊 1. Sales & Margin Audit</span>
            <span class="mm-step-pill">🎯 2. Trend & Event Strategy</span>
            <span class="mm-step-pill">✍️ 3. Bilingual Copy (Eng + Roman Urdu)</span>
            <span class="mm-step-pill">🛡️ 4. Guarded Queue Scheduling</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─── Execution Trigger ────────────────────────────────────────────────────────

run_col1, run_col2 = st.columns([2, 5])

with run_col1:
    launch_btn = st.button("🚀 Plan This Week's Marketing", type="primary", use_container_width=True)

with run_col2:
    st.markdown(
        "<div style='color: #CBD5E1; font-size: 0.9rem; padding-top: 8px;'>"
        "Click to trigger the 4-agent CrewAI pipeline. Posts are checked by Safety Guards before saving to the approval queue."
        "</div>",
        unsafe_allow_html=True,
    )

if launch_btn:
    with st.spinner("🤖 MarketMate CrewAI agents are analyzing your store and generating campaigns…"):
        try:
            data = main()
            st.session_state["campaign_data"] = data
            st.rerun()

        except LLMFailedError as exc:
            st.error(
                "**🚫 AI Pipeline Notice**\n\n"
                f"{exc}\n\n"
                "---\n"
                "**Your existing scheduled and pending posts are safe and unchanged.** "
                "You can click **Load Cached Result** in the sidebar to view the offline demo."
            )
        except Exception as exc:  # noqa: BLE001
            st.error(
                f"**Unexpected error:** {exc}\n\n"
                "Existing posts remain completely safe. Please try again."
            )

# ─── Campaign Output Section ──────────────────────────────────────────────────

if "campaign_data" in st.session_state:
    data = st.session_state["campaign_data"]

    # Status Banner
    if data.get("from_cache"):
        st.markdown(
            f"""
            <div class="demo-banner">
                📦 <strong>Demo Mode — Showing Cached Snapshot</strong> (saved on {data.get('cached_at', 'unknown date')}).
                This is a verified campaign plan loaded from local cache without incurring API tokens.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="success-banner">
                ✅ <strong>Live Campaign Plan Generated Successfully!</strong>
                All safety guards passed. Copy has been reviewed and queued for scheduling.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Organized Tabbed View
    tab_plan, tab_advisory = st.tabs(["📋 Campaign Strategy & Copy", "🛡️ Language & Quality Advisory"])

    with tab_plan:
        st.markdown(data["result"])

    with tab_advisory:
        quality_issues = data.get("quality_issues", {})
        if quality_issues:
            st.warning("The following advisory checks were flagged for review:")
            for section, issues in quality_issues.items():
                st.markdown(f"**Section: `{section}`**")
                for issue in issues:
                    st.markdown(f"- {issue}")
            st.caption("These checks are advisory. Review generated copy before one-click publishing.")
        else:
            st.success("🎉 No language quality or formatting issues detected in this campaign!")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ─── Marketing Approval Queue ─────────────────────────────────────────────────

st.markdown(
    """
    <div style="margin-bottom: 18px;">
        <h2 style="font-size: 1.55rem; font-weight: 800; color: #FFFFFF !important; margin-bottom: 6px;">
            📋 Marketing Post Approval Queue
        </h2>
        <div style="color: #CBD5E1 !important; font-size: 0.92rem;">
            Review, approve, or reject social media posts before publishing. Low-stock products and fake claims are automatically blocked.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Fetch all posts to calculate real-time stats
all_posts = get_post_queue()
total_cnt = len(all_posts)
pending_cnt = sum(1 for p in all_posts if p["status"] == "Pending")
approved_cnt = sum(1 for p in all_posts if p["status"] == "Approved")
rejected_cnt = sum(1 for p in all_posts if p["status"] == "Rejected")

# Stat Bar
stat_c1, stat_c2, stat_c3, stat_c4 = st.columns(4)

with stat_c1:
    st.markdown(
        f"""
        <div class="stat-box">
            <div class="stat-label">Total Posts</div>
            <div class="stat-num">{total_cnt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with stat_c2:
    st.markdown(
        f"""
        <div class="stat-box" style="border-color: #D97706;">
            <div class="stat-label" style="color: #FDE68A !important;">🟡 Pending Review</div>
            <div class="stat-num" style="color: #FCD34D !important;">{pending_cnt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with stat_c3:
    st.markdown(
        f"""
        <div class="stat-box" style="border-color: #059669;">
            <div class="stat-label" style="color: #A7F3D0 !important;">🟢 Approved</div>
            <div class="stat-num" style="color: #6EE7B7 !important;">{approved_cnt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with stat_c4:
    st.markdown(
        f"""
        <div class="stat-box" style="border-color: #DC2626;">
            <div class="stat-label" style="color: #FECACA !important;">🔴 Rejected</div>
            <div class="stat-num" style="color: #FCA5A5 !important;">{rejected_cnt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# Filter Controls
filter_col1, filter_col2 = st.columns([3, 1])

with filter_col1:
    status_filter = st.radio(
        "Filter queue by status:",
        options=["All", "Pending", "Approved", "Rejected"],
        horizontal=True,
        key="queue_status_filter",
    )

with filter_col2:
    st.write("")  # alignment spacer

# Query filtered posts
queue_status = None if status_filter == "All" else status_filter
display_posts = get_post_queue(status=queue_status)

if not display_posts:
    st.info(f"No posts found with status **{status_filter}**.")
else:
    for post in display_posts:
        p_status = post["status"]
        badge_cls = {
            "Pending": "badge-pending",
            "Approved": "badge-approved",
            "Rejected": "badge-rejected",
        }.get(p_status, "badge-pending")

        status_emoji = {"Pending": "🟡", "Approved": "🟢", "Rejected": "🔴"}.get(p_status, "⚪")

        st.markdown(
            f"""
            <div class="post-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                    <div>
                        <span style="font-size: 1.22rem; font-weight: 800; color: #FFFFFF !important;">
                            {post['product']}
                        </span>
                        &nbsp;&nbsp;
                        <span class="badge badge-platform">{post['platform']}</span>
                        &nbsp;&nbsp;
                        <span class="badge badge-time">📅 {post['scheduled_date']} @ {post['scheduled_time']}</span>
                        &nbsp;&nbsp;
                        <span class="badge badge-time">🏷️ {post['content_type']}</span>
                    </div>
                    <div>
                        <span class="badge {badge_cls}">{status_emoji} {p_status}</span>
                    </div>
                </div>
                <div class="post-content-box">{post['content']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Action Buttons (only show when status is Pending, or let user change status)
        action_col1, action_col2, action_spacer = st.columns([1, 1, 6])

        if p_status == "Pending":
            with action_col1:
                if st.button("✅ Approve", key=f"app_{post['id']}", use_container_width=True):
                    update_post_status(post["id"], "Approved")
                    st.rerun()
            with action_col2:
                if st.button("❌ Reject", key=f"rej_{post['id']}", use_container_width=True):
                    update_post_status(post["id"], "Rejected")
                    st.rerun()
        else:
            with action_col1:
                if st.button("↩️ Reset to Pending", key=f"rst_{post['id']}", use_container_width=True):
                    update_post_status(post["id"], "Pending")
                    st.rerun()

        st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)