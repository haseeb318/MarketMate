import streamlit as st

from crew import main
from tools.market_tools import (
    get_post_queue,
    update_post_status,
)


st.set_page_config(
    page_title="MarketMate",
    page_icon="📈",
    layout="wide",
)


st.title("📈 MarketMate")
st.subheader("AI Marketing Agent for E-commerce")

st.write(
    "Plan your weekly marketing campaign using sales, inventory, "
    "profit margins, and upcoming events."
)


if st.button("🚀 Plan This Week's Marketing", type="primary"):
    with st.spinner("MarketMate is analyzing your store..."):
        try:
            result = main()

            st.success("Marketing plan generated!")

            st.subheader("📋 Campaign Result")
            st.write(result)

        except Exception as e:
            st.error(f"Something went wrong: {e}")


st.divider()

st.subheader("📋 Marketing Approval Queue")

posts = get_post_queue()

if not posts:
    st.info("No posts are waiting for approval.")

else:
    for post in posts:
        st.markdown(f"### {post['product']} — {post['platform']}")

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
        