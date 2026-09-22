"""
UAE Retail & Logistics Analytics Dashboard
--------------------------------------------
A Streamlit dashboard sitting on top of the SQLite data warehouse built by
python/generate_data.py + python/etl.py. Designed to demonstrate the kind of
end-to-end analysis (sales, customer segmentation, delivery performance) a
Business/Data Analyst would deliver for a UAE-based retail & logistics MNC.

Run with:  streamlit run dashboard/app.py
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page config & styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="UAE Retail & Logistics Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#0B2545"     # deep navy — trust, corporate
ACCENT = "#12A594"      # teal — logistics / movement
GOLD = "#C9A24B"        # muted gold — used sparingly for VIP/highlight only
BG = "#F7F8FA"
CARD_BG = "#FFFFFF"
MUTED = "#5B6472"

CHART_COLORS = [PRIMARY, ACCENT, GOLD, "#6B7F99", "#8FD3C7", "#D9C89E"]

st.markdown(f"""
<style>
    .stApp {{ background-color: {BG}; }}
    h1, h2, h3 {{ color: {PRIMARY}; font-family: 'Helvetica Neue', sans-serif; }}
    div[data-testid="stMetric"] {{
        background-color: {CARD_BG};
        border: 1px solid #E5E8EC;
        border-left: 4px solid {ACCENT};
        border-radius: 6px;
        padding: 14px 18px;
    }}
    div[data-testid="stMetricLabel"] {{ color: {MUTED}; font-size: 13px; }}
    .section-divider {{
        height: 1px;
        background: linear-gradient(90deg, {PRIMARY}, {ACCENT}, transparent);
        margin: 18px 0 22px 0;
        border: none;
    }}
    .header-banner {{
        background: linear-gradient(120deg, {PRIMARY} 0%, #163B6D 60%, {ACCENT} 130%);
        padding: 26px 32px;
        border-radius: 10px;
        margin-bottom: 24px;
    }}
    .header-banner h1 {{ color: white; margin: 0; font-size: 28px; }}
    .header-banner p {{ color: #C9D6E8; margin: 4px 0 0 0; font-size: 14px; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "uae_retail.db")


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    customers = pd.read_sql("SELECT * FROM customers", conn, parse_dates=["signup_date"])
    orders = pd.read_sql("SELECT * FROM orders", conn, parse_dates=["order_date"])
    order_items = pd.read_sql("SELECT * FROM order_items", conn)
    products = pd.read_sql("SELECT * FROM products", conn)
    warehouses = pd.read_sql("SELECT * FROM warehouses", conn)
    deliveries = pd.read_sql(
        "SELECT * FROM deliveries", conn,
        parse_dates=["dispatch_date", "promised_date", "delivery_date"]
    )
    suppliers = pd.read_sql("SELECT * FROM suppliers", conn)
    conn.close()
    return customers, orders, order_items, products, warehouses, deliveries, suppliers


customers, orders, order_items, products, warehouses, deliveries, suppliers = load_data()

# Merge convenience frame: order line items with order + customer context
order_full = (
    order_items
    .merge(orders, on="order_id")
    .merge(customers, on="customer_id")
    .merge(products, on="product_id", suffixes=("", "_prod"))
)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

min_date, max_date = orders.order_date.min(), orders.order_date.max()
date_range = st.sidebar.date_input(
    "Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date, end_date = min_date, max_date

emirates_sel = st.sidebar.multiselect(
    "Emirate", options=sorted(customers.emirate.unique()), default=sorted(customers.emirate.unique())
)
channel_sel = st.sidebar.multiselect(
    "Channel", options=sorted(orders.channel.unique()), default=sorted(orders.channel.unique())
)
segment_sel = st.sidebar.multiselect(
    "Customer Segment", options=sorted(customers.customer_segment.unique()),
    default=sorted(customers.customer_segment.unique())
)

mask = (
    (order_full.order_date >= start_date) & (order_full.order_date <= end_date) &
    (order_full.emirate.isin(emirates_sel)) &
    (order_full.channel.isin(channel_sel)) &
    (order_full.customer_segment.isin(segment_sel))
)
f = order_full.loc[mask].copy()

st.sidebar.markdown("---")
st.sidebar.caption(
    "Synthetic dataset · 3,000 customers · 18,000 orders · 7 Emirates\n\n"
    "Built with SQLite + pandas + Streamlit + Plotly"
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="header-banner">
    <h1>UAE Retail &amp; Logistics Analytics</h1>
    <p>Sales performance, customer value, and last-mile delivery across the seven Emirates</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Top KPIs
# ---------------------------------------------------------------------------
total_revenue = f.line_total_aed.sum()
total_orders = f.order_id.nunique()
aov = total_revenue / total_orders if total_orders else 0
active_customers = f.customer_id.nunique()

del_f = deliveries[deliveries.order_id.isin(f.order_id.unique())]
on_time_pct = (del_f.on_time.sum() / len(del_f) * 100) if len(del_f) else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Revenue", f"AED {total_revenue:,.0f}")
c2.metric("Total Orders", f"{total_orders:,}")
c3.metric("Avg Order Value", f"AED {aov:,.0f}")
c4.metric("Active Customers", f"{active_customers:,}")
c5.metric("On-Time Delivery", f"{on_time_pct:.1f}%")

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Sales & Revenue", "🧑‍🤝‍🧑 Customer Insights", "🚚 Delivery Performance", "🛍️ Product Mix"]
)

# ===== TAB 1: Sales & Revenue ==============================================
with tab1:
    col1, col2 = st.columns((2, 1))

    with col1:
        monthly = (
            f.assign(month=f.order_date.dt.to_period("M").astype(str))
            .groupby("month")
            .agg(revenue=("line_total_aed", "sum"), orders=("order_id", "nunique"))
            .reset_index()
        )
        fig = go.Figure()
        fig.add_trace(go.Bar(x=monthly.month, y=monthly.revenue, name="Revenue (AED)",
                              marker_color=PRIMARY, yaxis="y1"))
        fig.add_trace(go.Scatter(x=monthly.month, y=monthly.orders, name="Orders",
                                  mode="lines+markers", line=dict(color=ACCENT, width=3), yaxis="y2"))
        fig.update_layout(
            title="Monthly Revenue & Order Volume",
            yaxis=dict(title="Revenue (AED)"),
            yaxis2=dict(title="Orders", overlaying="y", side="right"),
            legend=dict(orientation="h", y=1.15),
            height=420, plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        emirate_rev = f.groupby("emirate", as_index=False).line_total_aed.sum().sort_values("line_total_aed")
        fig2 = px.bar(emirate_rev, x="line_total_aed", y="emirate", orientation="h",
                       title="Revenue by Emirate", color_discrete_sequence=[ACCENT])
        fig2.update_layout(height=420, plot_bgcolor="white", paper_bgcolor="white",
                            xaxis_title="Revenue (AED)", yaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        chan = f.groupby("channel", as_index=False).agg(
            revenue=("line_total_aed", "sum"), orders=("order_id", "nunique")
        )
        fig3 = px.pie(chan, names="channel", values="revenue", title="Revenue Share by Channel",
                       color_discrete_sequence=CHART_COLORS, hole=0.45)
        fig3.update_layout(height=380)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        pay = f.groupby("payment_method", as_index=False).line_total_aed.sum().sort_values("line_total_aed", ascending=False)
        fig4 = px.bar(pay, x="payment_method", y="line_total_aed", title="Revenue by Payment Method",
                       color_discrete_sequence=[PRIMARY])
        fig4.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                            xaxis_title="", yaxis_title="Revenue (AED)")
        st.plotly_chart(fig4, use_container_width=True)

# ===== TAB 2: Customer Insights (RFM + Cohorts) ============================
with tab2:
    st.subheader("RFM Segmentation")
    st.caption("Recency, Frequency, Monetary scoring — identifies VIP, loyal, at-risk, and churned customers.")

    ref_date = f.order_date.max()
    rfm = (
        f.groupby("customer_id")
        .agg(last_order=("order_date", "max"),
             frequency=("order_id", "nunique"),
             monetary=("line_total_aed", "sum"))
        .reset_index()
    )
    rfm["recency_days"] = (ref_date - rfm.last_order).dt.days
    rfm["r_score"] = pd.qcut(rfm.recency_days.rank(method="first", ascending=False), 4, labels=[1, 2, 3, 4]).astype(int)
    rfm["f_score"] = pd.qcut(rfm.frequency.rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    rfm["m_score"] = pd.qcut(rfm.monetary.rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    rfm["rfm_total"] = rfm.r_score + rfm.f_score + rfm.m_score

    def segment(row):
        if row.rfm_total >= 10:
            return "Champions / VIP"
        elif row.rfm_total >= 7:
            return "Loyal Customers"
        elif row.rfm_total >= 5:
            return "At Risk"
        return "Churned / Low Value"

    rfm["segment"] = rfm.apply(segment, axis=1)

    col1, col2 = st.columns((1, 2))
    with col1:
        seg_counts = rfm.segment.value_counts().reset_index()
        seg_counts.columns = ["segment", "customers"]
        fig5 = px.pie(seg_counts, names="segment", values="customers", title="Customer Segments (RFM)",
                       color_discrete_sequence=CHART_COLORS, hole=0.4)
        st.plotly_chart(fig5, use_container_width=True)
    with col2:
        seg_value = rfm.groupby("segment", as_index=False).monetary.sum().sort_values("monetary", ascending=False)
        fig6 = px.bar(seg_value, x="segment", y="monetary", title="Lifetime Revenue by Segment",
                       color_discrete_sequence=[PRIMARY])
        fig6.update_layout(plot_bgcolor="white", paper_bgcolor="white", yaxis_title="Revenue (AED)", xaxis_title="")
        st.plotly_chart(fig6, use_container_width=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("Monthly Cohort Retention")
    st.caption("Of customers who first purchased in a given month, how many were still active N months later?")

    first_purchase = orders.groupby("customer_id").order_date.min().dt.to_period("M")
    cohort_df = orders.copy()
    cohort_df["cohort_month"] = cohort_df.customer_id.map(first_purchase)
    cohort_df["order_period"] = cohort_df.order_date.dt.to_period("M")
    cohort_df["month_index"] = (cohort_df.order_period - cohort_df.cohort_month).apply(lambda x: x.n)

    cohort_pivot = (
        cohort_df.groupby(["cohort_month", "month_index"]).customer_id.nunique().reset_index()
        .pivot(index="cohort_month", columns="month_index", values="customer_id")
    )
    cohort_size = cohort_pivot[0]
    retention = cohort_pivot.divide(cohort_size, axis=0).round(3) * 100
    retention.index = retention.index.astype(str)

    fig7 = px.imshow(
        retention.iloc[:, :12], text_auto=".0f", aspect="auto",
        color_continuous_scale=[[0, "#F7F8FA"], [1, PRIMARY]],
        labels=dict(x="Months since first purchase", y="Cohort month", color="Retention %"),
        title="Retention Heatmap (%)"
    )
    fig7.update_layout(height=500)
    st.plotly_chart(fig7, use_container_width=True)

# ===== TAB 3: Delivery Performance ==========================================
with tab3:
    st.subheader("Last-Mile Delivery Performance")

    del_join = deliveries.merge(warehouses, on="warehouse_id").merge(orders[["order_id", "channel"]], on="order_id")
    del_join = del_join[del_join.order_id.isin(f.order_id.unique())]
    delivered = del_join[del_join.delivery_status == "Delivered"].copy()
    delivered["delivery_days"] = (delivered.delivery_date - delivered.dispatch_date).dt.total_seconds() / 86400

    col1, col2 = st.columns(2)
    with col1:
        by_emirate = delivered.groupby("emirate", as_index=False).agg(
            on_time_pct=("on_time", lambda x: 100 * x.mean()),
            avg_days=("delivery_days", "mean"),
        ).sort_values("on_time_pct")
        fig8 = px.bar(by_emirate, x="on_time_pct", y="emirate", orientation="h",
                       title="On-Time Delivery % by Emirate", color_discrete_sequence=[ACCENT])
        fig8.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_title="On-time %", yaxis_title="")
        st.plotly_chart(fig8, use_container_width=True)

    with col2:
        by_courier = delivered.groupby("courier", as_index=False).agg(
            on_time_pct=("on_time", lambda x: 100 * x.mean()),
            deliveries=("delivery_id", "count"),
        ).sort_values("on_time_pct", ascending=False)
        fig9 = px.bar(by_courier, x="courier", y="on_time_pct", title="On-Time Delivery % by Courier",
                       color_discrete_sequence=[PRIMARY], text="deliveries")
        fig9.update_layout(plot_bgcolor="white", paper_bgcolor="white", yaxis_title="On-time %", xaxis_title="")
        st.plotly_chart(fig9, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        status_counts = del_join.delivery_status.value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig10 = px.pie(status_counts, names="status", values="count", title="Delivery Outcome Breakdown",
                        color_discrete_sequence=CHART_COLORS, hole=0.45)
        st.plotly_chart(fig10, use_container_width=True)
    with col4:
        fig11 = px.histogram(delivered, x="delivery_days", nbins=15, title="Delivery Time Distribution (days)",
                              color_discrete_sequence=[ACCENT])
        fig11.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_title="Days from dispatch", yaxis_title="Deliveries")
        st.plotly_chart(fig11, use_container_width=True)

    st.info(
        "💡 **Insight**: Emirates further from major warehouses (Fujairah, RAK, UAQ) tend to show lower "
        "on-time rates — a natural candidate for a regional micro-fulfillment hub recommendation."
    )

# ===== TAB 4: Product Mix ===================================================
with tab4:
    col1, col2 = st.columns(2)
    with col1:
        cat_rev = f.groupby("category", as_index=False).line_total_aed.sum().sort_values("line_total_aed", ascending=False)
        fig12 = px.bar(cat_rev, x="category", y="line_total_aed", title="Revenue by Category",
                        color_discrete_sequence=[PRIMARY])
        fig12.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_title="", yaxis_title="Revenue (AED)")
        st.plotly_chart(fig12, use_container_width=True)
    with col2:
        top_products = (
            f.groupby("product_name", as_index=False)
            .agg(revenue=("line_total_aed", "sum"), units=("quantity", "sum"))
            .sort_values("revenue", ascending=False).head(10)
        )
        fig13 = px.bar(top_products.sort_values("revenue"), x="revenue", y="product_name", orientation="h",
                        title="Top 10 Products by Revenue", color_discrete_sequence=[ACCENT])
        fig13.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_title="Revenue (AED)", yaxis_title="")
        st.plotly_chart(fig13, use_container_width=True)

    st.subheader("Discounting Behavior by Category")
    disc = f.groupby("category", as_index=False).discount_pct.mean().sort_values("discount_pct", ascending=False)
    fig14 = px.bar(disc, x="category", y="discount_pct", title="Average Discount % by Category",
                    color_discrete_sequence=[GOLD])
    fig14.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_title="", yaxis_title="Avg Discount %")
    st.plotly_chart(fig14, use_container_width=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.caption("Portfolio project — synthetic data generated to model a UAE retail & logistics business. Built with SQLite, pandas, Streamlit & Plotly.")
