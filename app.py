"""
MarketMate – app.py
Streamlit front-end.

Phase 8 additions
─────────────────
- Sidebar shows STOCK_THRESHOLD and MAX_POSTS_PER_DAY for transparency.
- Sidebar ‘Demo / Offline Mode’ panel lets users load the cached result with
  one click even when the API is unavailable.
- Cached results are marked with a visible banner so the demo is honest.
- Language quality issues from review_campaign_content() are surfaced as an
  expandable advisory block below the campaign output.
- LLMFailedError is caught and shown as a clear, friendly message that
  reassures the user that existing posts are unchanged.
- Approval queue now has a status filter (All / Pending / Approved / Rejected)
  with colour-coded badges so the queue is not cluttered.
"""
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

# ─── Page config ──────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MarketMate",
    page_icon="📈",
    layout="wide",
)

# ─── Sidebar: safety settings + offline / demo mode ───────────────────────────

with st.sidebar:
    st.header("⚙️ Safety Settings")
    st.metric(
        "Stock Threshold",
        f"{STOCK_THRESHOLD} units",
        help=(
            "Posts for products with stock below this level are automatically blocked "
            "before they reach the database."
        ),
    )
    st.metric(
        "Daily Posting Cap",
        f"{MAX_POSTS_PER_DAY} posts / day",
        help="Maximum number of non-rejected posts per scheduled calendar day.",
    )

    st.divider()

    st.subheader("🗂️ Demo / Offline Mode")
    cached = load_fallback()
    if cached:
        st.success(
            f"Cached result available \n(saved {cached.get('saved_at', 'unknown date')})"
        )
        if st.button("📥 Load Cached Result", key="load_cache_btn"):
            quality_issues = review_campaign_content(cached["result"])
            st.session_state["campaign_data"] = {
                "result": cached["result"],
                "from_cache": True,
                "cached_at": cached.get("saved_at"),
                "quality_issues": quality_issues,
            }
            st.rerun()
    else:
        st.info(
            "No cached result yet.\nRun the campaign once to create an offline snapshot."
        )

# ─── Main header ────────────────────────────────────────────────────────────

st.title("📈 MarketMate")
st.subheader("AI Marketing Agent for E-commerce")
st.write(
    "Plan your weekly marketing campaign using sales, inventory, "
    "profit margins, and upcoming events."
)

# ─── Campaign trigger ──────────────────────────────────────────────────────────

if st.button("🚀 Plan This Week's Marketing", type="primary"):
    with st.spinner("MarketMate is analysing your store…"):
        try:
            data = main()
            st.session_state["campaign_data"] = data
            st.rerun()

        except LLMFailedError as exc:
            st.error(
                "**🚫 AI Pipeline Failed**\n\n"
                f"{exc}\n\n"
                "---\n"
                "**Your existing scheduled and pending posts are safe and unchanged.** "
                "Use the *Load Cached Result* button in the sidebar for a demo."
            )
        except Exception as exc:  # noqa: BLE001
            st.error(
                f"**Unexpected error:** {exc}\n\n"
                "Your existing posts are unchanged. Please try again."
            )

# ─── Campaign result display ──────────────────────────────────────────────────────

if "campaign_data" in st.session_state:
    data = st.session_state["campaign_data"]

    # Cache banner
    if data.get("from_cache"):
        st.warning(
            f"📦 **Demo Mode — Showing Cached Result** "
            f"(saved on {data.get('cached_at', 'unknown date')}).  "
            "This is a previously saved campaign plan, not a live LLM output."
        )
    else:
        st.success("✅ Live campaign plan generated successfully!")

    # Language quality advisory
    quality_issues = data.get("quality_issues", {})
    if quality_issues:
        with st.expander(
            "⚠️ Language Quality Issues Detected — click to review",
            expanded=True,
        ):
            for section, issues in quality_issues.items():
                st.markdown(f"**{section}**")
                for issue in issues:
                    st.markdown(f"- {issue}")
            st.caption(
                "These are advisory notices only. "
                "Review and edit the copy below before publishing."
            )

    st.subheader("📋 Campaign Result")
    st.write(data["result"])


st.divider()

# ─── Approval queue ───────────────────────────────────────────────────────────────

st.subheader("📋 Marketing Approval Queue")

status_filter = st.radio(
    "Filter by status:",
    options=["All", "Pending", "Approved", "Rejected"],
    horizontal=True,
    key="queue_status_filter",
)

queue_status = None if status_filter == "All" else status_filter
posts = get_post_queue(status=queue_status)

_STATUS_ICON = {
    "Pending": "🟡",
    "Approved": "🟢",
    "Rejected": "🔴",
}

if not posts:
    st.info("No posts match the selected filter.")
else:
    for post in posts:
        icon = _STATUS_ICON.get(post["status"], "⚪")
        st.markdown(f"### {icon} {post['product']} — {post['platform']}")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"**Scheduled:** {post['scheduled_date']} at {post['scheduled_time']}")
            st.write(f"**Content type:** {post['content_type']}")
            st.write(f"**Status:** {post['status']}")
            st.write(f"**Content:** {post['content']}")

        with col2:
            if post["status"] == "Pending":
                if st.button("✅ Approve", key=f"approve_{post['id']}"):
                    update_post_status(post["id"], "Approved")
                    st.rerun()

                if st.button("❌ Reject", key=f"reject_{post['id']}"):
                    update_post_status(post["id"], "Rejected")
                    st.rerun()

        st.divider()