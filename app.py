import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import zipfile
import io

st.set_page_config(
    page_title="NOVA Sales Intelligence",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
.stApp {background:#0b1020;color:#f4f7ff}
[data-testid="stMetric"] {
    background:#171f33;
    padding:18px;
    border-radius:12px;
    border:1px solid #293550;
}
</style>
""", unsafe_allow_html=True)

st.title("🚀 NOVA Sales Intelligence")
st.caption("ELECTRONICS • SALES • BUSINESS INTELLIGENCE")

DATA_DIR = Path(__file__).parent / "data" / "data"

def read_csv_bytes(name, content):
    try:
        return pd.read_csv(io.BytesIO(content))
    except Exception:
        return None

@st.cache_data
def load_repo_data():
    frames = []
    if DATA_DIR.exists():
        for path in DATA_DIR.rglob("*.csv"):
            try:
                frames.append(pd.read_csv(path))
            except Exception:
                pass
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

df = load_repo_data()

with st.sidebar:
    st.header("Dashboard Filters")
    st.caption("You can use sample CSV files committed in the repository, or upload CSV/ZIP files.")
    uploaded = st.file_uploader(
        "Upload sales CSV or ZIP",
        type=["csv", "zip"],
        accept_multiple_files=False
    )

if uploaded is not None:
    try:
        if uploaded.name.lower().endswith(".csv"):
            new_df = read_csv_bytes(uploaded.name, uploaded.getvalue())
            if new_df is not None:
                df = new_df
        else:
            frames = []
            with zipfile.ZipFile(io.BytesIO(uploaded.getvalue())) as z:
                for name in z.namelist():
                    if name.lower().endswith(".csv") and not name.startswith("__MACOSX/"):
                        try:
                            frames.append(pd.read_csv(z.open(name)))
                        except Exception:
                            pass
            if frames:
                df = pd.concat(frames, ignore_index=True)
    except Exception as e:
        st.error(f"Could not read the uploaded file: {e}")

if df.empty:
    st.info(
        "No dataset is included yet. Upload the electronics_sales_separated_categories.zip "
        "file or a CSV using the sidebar to view the dashboard."
    )
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding:20px;">
        <h3>Developed by Ahmed Sharaf</h3>
        <p>AI Student | Data Analytics</p>
        <p>© 2026 NOVA Sales Intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

required = ["Revenue_EGP", "Profit_EGP", "Quantity"]
missing = [col for col in required if col not in df.columns]
if missing:
    st.error(f"Dataset is missing required columns: {', '.join(missing)}")
    st.stop()

for col in required:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

filtered = df.copy()

with st.sidebar:
    if "Category" in filtered.columns:
        categories = sorted(filtered["Category"].dropna().astype(str).unique())
        selected_categories = st.multiselect(
            "Product Category", categories, default=categories
        )
        filtered = filtered[filtered["Category"].astype(str).isin(selected_categories)]

    if "Region" in filtered.columns:
        regions = sorted(filtered["Region"].dropna().astype(str).unique())
        selected_regions = st.multiselect(
            "Region", regions, default=regions
        )
        filtered = filtered[filtered["Region"].astype(str).isin(selected_regions)]

revenue = filtered["Revenue_EGP"].sum()
profit = filtered["Profit_EGP"].sum()
units = filtered["Quantity"].sum()
orders = filtered["Order_ID"].nunique() if "Order_ID" in filtered.columns else len(filtered)
margin = profit / revenue * 100 if revenue else 0

a, b, c, d, e = st.columns(5)
a.metric("Total Revenue", f"{revenue:,.0f} EGP")
b.metric("Total Profit", f"{profit:,.0f} EGP")
c.metric("Units Sold", f"{units:,.0f}")
d.metric("Orders", f"{orders:,}")
e.metric("Profit Margin", f"{margin:.1f}%")

left, right = st.columns(2)
with left:
    st.subheader("Revenue by Category")
    if "Category" in filtered.columns:
        chart = filtered.groupby("Category", as_index=False)["Revenue_EGP"].sum()
        fig = px.bar(chart, x="Category", y="Revenue_EGP", color="Category", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Profit by Brand")
    if "Brand" in filtered.columns:
        chart = filtered.groupby("Brand", as_index=False)["Profit_EGP"].sum()
        chart = chart.sort_values("Profit_EGP", ascending=False).head(10)
        fig = px.bar(chart, x="Brand", y="Profit_EGP", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Top 10 Products by Profit")
    if "Product" in filtered.columns:
        top = filtered.groupby("Product", as_index=False)["Profit_EGP"].sum().nlargest(10, "Profit_EGP")
        fig = px.bar(top, x="Profit_EGP", y="Product", orientation="h", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Revenue by Region")
    if "Region" in filtered.columns:
        chart = filtered.groupby("Region", as_index=False)["Revenue_EGP"].sum()
        fig = px.pie(chart, names="Region", values="Revenue_EGP", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

if "Order_Date" in filtered.columns:
    st.subheader("Monthly Revenue")
    dates = pd.to_datetime(filtered["Order_Date"], errors="coerce")
    monthly = filtered.assign(Month=dates.dt.to_period("M").astype(str))
    monthly = monthly[monthly["Month"] != "NaT"]
    monthly = monthly.groupby("Month", as_index=False)["Revenue_EGP"].sum().sort_values("Month")
    if not monthly.empty:
        fig = px.line(monthly, x="Month", y="Revenue_EGP", markers=True, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Sales Records")
st.dataframe(filtered, use_container_width=True)

st.download_button(
    "Download Filtered Data (CSV)",
    filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="nova_sales_results.csv",
    mime="text/csv"
)

st.caption("NOVA Sales Intelligence | Portfolio Demo")
st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:20px;">
    <h3>Developed by Ahmed Sharaf</h3>
    <p>AI Student | Data Analytics</p>
    <p>© 2026 NOVA Sales Intelligence</p>
</div>
""", unsafe_allow_html=True)
