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
.stApp {
    background-color: #0b1020;
    color: #f4f7ff;
}
[data-testid="stMetric"] {
    background-color: #171f33;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #293550;
}
</style>
""", unsafe_allow_html=True)

st.title("🚀 NOVA Sales Intelligence")
st.caption("ELECTRONICS • SALES • BUSINESS INTELLIGENCE")

DATA_DIR = Path(__file__).parent / "data" / "data"


def read_csv_bytes(content):
    try:
        return pd.read_csv(io.BytesIO(content))
    except Exception as e:
        st.error(f"Could not read CSV file: {e}")
        return None


@st.cache_data
def load_repo_data():
    frames = []

    if not DATA_DIR.exists():
        return pd.DataFrame(), []

    csv_files = sorted(DATA_DIR.rglob("*.csv"))

    for path in csv_files:
        try:
            temp = pd.read_csv(path)
            if not temp.empty:
                frames.append(temp)
        except Exception as e:
            print(f"Error reading {path.name}: {e}")

    if frames:
        combined = pd.concat(
            frames,
            ignore_index=True,
            sort=False
        )
    else:
        combined = pd.DataFrame()

    return combined, [str(path) for path in csv_files]


df, csv_files = load_repo_data()

with st.expander("Dataset Information"):
    st.write("Data folder:", str(DATA_DIR))
    st.write("CSV files found:", len(csv_files))
    st.write("Rows loaded:", len(df))
    if csv_files:
        st.write("Files:", csv_files)


with st.sidebar:
    st.header("Dashboard Filters")
    st.caption("Upload a CSV or ZIP file, or use the repository datasets.")

    uploaded = st.file_uploader(
        "Upload Sales CSV or ZIP",
        type=["csv", "zip"]
    )


if uploaded is not None:
    try:
        if uploaded.name.lower().endswith(".csv"):
            new_df = read_csv_bytes(uploaded.getvalue())
            if new_df is not None:
                df = new_df
                st.sidebar.success("CSV loaded successfully.")

        elif uploaded.name.lower().endswith(".zip"):
            frames = []

            with zipfile.ZipFile(
                io.BytesIO(uploaded.getvalue())
            ) as archive:

                csv_names = [
                    name for name in archive.namelist()
                    if name.lower().endswith(".csv")
                    and not name.startswith("__MACOSX/")
                    and not Path(name).name.startswith("._")
                ]

                for name in csv_names:
                    try:
                        with archive.open(name) as file:
                            temp = pd.read_csv(file)

                        if not temp.empty:
                            frames.append(temp)

                    except Exception as e:
                        st.warning(f"Could not read {name}: {e}")

            if frames:
                df = pd.concat(
                    frames,
                    ignore_index=True,
                    sort=False
                )
                st.sidebar.success(
                    f"Loaded {len(frames)} CSV file(s)."
                )
            else:
                st.sidebar.error("No readable CSV files found in ZIP.")

    except zipfile.BadZipFile:
        st.error("The uploaded ZIP file is invalid or corrupted.")
    except Exception as e:
        st.error(f"Could not process uploaded file: {e}")


if df.empty:
    st.info(
        "No dataset is available. Make sure CSV files are inside "
        "data/data, or upload a CSV/ZIP file using the sidebar."
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
    st.error(
        "Dataset is missing required columns: "
        + ", ".join(missing)
    )
    st.stop()


for col in required:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    ).fillna(0)


filtered = df.copy()

with st.sidebar:
    if "Category" in filtered.columns:
        categories = sorted(
            filtered["Category"].dropna().astype(str).unique().tolist()
        )
        selected_categories = st.multiselect(
            "Product Category",
            categories,
            default=categories
        )
        filtered = filtered[
            filtered["Category"].astype(str).isin(selected_categories)
        ]

    if "Region" in filtered.columns:
        regions = sorted(
            filtered["Region"].dropna().astype(str).unique().tolist()
        )
        selected_regions = st.multiselect(
            "Region",
            regions,
            default=regions
        )
        filtered = filtered[
            filtered["Region"].astype(str).isin(selected_regions)
        ]


if filtered.empty:
    st.warning("No records match your selected filters.")
    st.stop()


revenue = filtered["Revenue_EGP"].sum()
profit = filtered["Profit_EGP"].sum()
units = filtered["Quantity"].sum()

orders = (
    filtered["Order_ID"].nunique()
    if "Order_ID" in filtered.columns
    else len(filtered)
)

margin = profit / revenue * 100 if revenue != 0 else 0

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
        chart = filtered.groupby(
            "Category", as_index=False
        )["Revenue_EGP"].sum()

        fig = px.bar(
            chart,
            x="Category",
            y="Revenue_EGP",
            color="Category",
            template="plotly_dark",
            title="Sales Revenue by Product Category"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Category column is not available.")


with right:
    st.subheader("Profit by Brand")

    if "Brand" in filtered.columns:
        chart = filtered.groupby(
            "Brand", as_index=False
        )["Profit_EGP"].sum()

        chart = chart.sort_values(
            "Profit_EGP", ascending=False
        ).head(10)

        fig = px.bar(
            chart,
            x="Brand",
            y="Profit_EGP",
            template="plotly_dark",
            title="Top Brands by Profit"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Brand column is not available.")


left, right = st.columns(2)

with left:
    st.subheader("Top 10 Products by Profit")

    if "Product" in filtered.columns:
        top = (
            filtered.groupby("Product", as_index=False)["Profit_EGP"]
            .sum()
            .nlargest(10, "Profit_EGP")
        )

        fig = px.bar(
            top,
            x="Profit_EGP",
            y="Product",
            orientation="h",
            template="plotly_dark",
            title="Most Profitable Products"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Product column is not available.")


with right:
    st.subheader("Revenue by Region")

    if "Region" in filtered.columns:
        chart = filtered.groupby(
            "Region", as_index=False
        )["Revenue_EGP"].sum()

        fig = px.pie(
            chart,
            names="Region",
            values="Revenue_EGP",
            template="plotly_dark",
            title="Revenue Distribution by Region"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Region column is not available.")


if "Order_Date" in filtered.columns:
    st.subheader("Monthly Revenue")

    dates = pd.to_datetime(
        filtered["Order_Date"],
        errors="coerce"
    )

    monthly_data = filtered.assign(
        Month=dates.dt.strftime("%Y-%m")
    ).dropna(subset=["Month"])

    monthly = (
        monthly_data.groupby("Month", as_index=False)["Revenue_EGP"]
        .sum()
        .sort_values("Month")
    )

    if not monthly.empty:
        fig = px.line(
            monthly,
            x="Month",
            y="Revenue_EGP",
            markers=True,
            template="plotly_dark",
            title="Monthly Sales Revenue"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No valid dates found in Order_Date.")


st.subheader("Sales Records")

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True
)

st.caption(
    f"Showing {len(filtered):,} records out of {len(df):,}."
)


csv_data = filtered.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="📥 Download Filtered Data (CSV)",
    data=csv_data,
    file_name="nova_sales_results.csv",
    mime="text/csv"
)


st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:20px;">
    <h3>Developed by Ahmed Sharaf</h3>
    <p>AI Student | Data Analytics</p>
    <p>© 2026 NOVA Sales Intelligence</p>
</div>
""", unsafe_allow_html=True)
