"""Dashboard for electrical energy analysis and forecasting in Colombia.

Streamlit application that walks through the full project pipeline: raw data,
transformations, outlier treatment, models (Prophet and ML), demand vs.
generation comparison, and energy policy conclusions.
"""

import os

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------- #
# General configuration
# --------------------------------------------------------------------------- #
DATA_PATH = os.path.join("data", "sample")
RESULTS_PATH = "results"
FIGURES_PATH = os.path.join("results", "figures")

GITHUB_URL = "https://github.com/santiagoarbolpiedra/proyecto-energia-electrica"

st.set_page_config(
    page_title="Electrical Energy Colombia",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 2.5rem; padding-bottom: 3rem;}
      [data-testid="stMetric"] {
          background: rgba(128, 128, 128, 0.08);
          border: 1px solid rgba(128, 128, 128, 0.18);
          border-radius: 0.75rem;
          padding: 1rem 1rem 0.75rem 1rem;
      }
      [data-testid="stMetricLabel"] {justify-content: center;}
      h1, h2, h3 {letter-spacing: -0.01em;}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Loading utilities (cached)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def load_sample(filename: str) -> pd.DataFrame:
    """Load a sample CSV from data/sample/."""
    try:
        return pd.read_csv(os.path.join(DATA_PATH, filename))
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load {filename}: {exc}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_result_csv(filename: str) -> pd.DataFrame:
    """Load a result CSV from results/."""
    try:
        return pd.read_csv(os.path.join(RESULTS_PATH, filename))
    except Exception:  # noqa: BLE001
        return pd.DataFrame()


def figure(name: str, caption: str) -> None:
    """Display a figure from results/figures/ with error handling."""
    path = os.path.join(FIGURES_PATH, name)
    if os.path.exists(path):
        st.image(path, caption=caption, width="stretch")
    else:
        st.warning(f"Chart '{name}' not found in results/figures/.")


def section_title(emoji: str, title: str, subtitle: str | None = None) -> None:
    """Consistent heading for each section."""
    st.title(f"{emoji}  {title}")
    if subtitle:
        st.caption(subtitle)
    st.divider()


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #
def page_home() -> None:
    st.title("⚡ Electrical Energy in Colombia")
    st.subheader("Demand and generation analysis and forecasting")
    st.write(
        "Interactive dashboard that walks through the entire project pipeline: from "
        "the raw data of the Colombian electrical system to time series modeling "
        "and conclusions on the risk of an energy deficit."
    )
    st.divider()

    st.markdown("#### Key indicators")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average demand", "≈ 241 GWh/day")
    c2.metric("R² generation (Prophet)", "0.77")
    c3.metric("R² generation (Ridge ML)", "0.76")
    c4.metric("R² demand (Prophet)", "0.22")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("##### 🎯 Objective")
            st.write(
                "Forecast national electrical demand and generation from official "
                "historical data (SIMEM, PARATEC/XM) to support decisions on the "
                "risk of a deficit towards 2027–2030."
            )
    with col_b:
        with st.container(border=True):
            st.markdown("##### 🧭 What you'll find here")
            st.markdown(
                "- Raw data and its transformation to daily GWh\n"
                "- Outlier treatment\n"
                "- Forecasting models (Prophet and ML regression)\n"
                "- Demand vs. generation comparison and conclusions"
            )

    st.info(
        "Use the menu on the left to navigate between the analysis sections.",
        icon="👈",
    )


def page_data() -> None:
    section_title(
        "📂", "Raw data",
        "Sample of demand and generation data (full files are downloaded from "
        "SIMEM; see data/README.md).",
    )

    tab_demand, tab_gen = st.tabs(["⚡ Demand", "🏭 Generation"])

    with tab_demand:
        df = load_sample("Demanda.csv")
        if not df.empty:
            c1, c2 = st.columns(2)
            c1.metric("Rows in sample", f"{len(df):,}")
            c2.metric("Columns", f"{df.shape[1]}")
            st.dataframe(df.head(15), width="stretch")
            if {"FechaHora", "Valor"}.issubset(df.columns):
                series = df.assign(FechaHora=pd.to_datetime(df["FechaHora"], errors="coerce"))
                series = series.dropna(subset=["FechaHora"]).set_index("FechaHora")["Valor"]
                st.markdown("**Hourly demand (sample)**")
                st.line_chart(series.sort_index(), height=260)
            st.download_button(
                "⬇️ Download Demanda.csv sample",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="Demanda_muestra.csv",
                mime="text/csv",
            )

    with tab_gen:
        df = load_sample("Generacion.csv")
        if not df.empty:
            c1, c2 = st.columns(2)
            c1.metric("Rows in sample", f"{len(df):,}")
            c2.metric("Columns", f"{df.shape[1]}")
            st.dataframe(df.head(15), width="stretch")
            st.download_button(
                "⬇️ Download Generacion.csv sample",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="Generacion_muestra.csv",
                mime="text/csv",
            )


def page_transformations() -> None:
    section_title("🔧", "Transformations",
                  "Standardization of the data to a common format: Date | Value (GWh).")

    st.markdown(
        "The main pipeline transformations are:\n"
        "- Date column conversion to **YYYY-MM-DD** format.\n"
        "- Energy conversion to **GWh** (e.g. MWh → GWh by dividing by 1,000).\n"
        "- **Daily** aggregation by summing the records for each day."
    )

    st.markdown("##### Example of the final table")
    example = pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=5, freq="D"),
        "Value_MWh": [89000, 102500, 95000, 87000, 120000],
    })
    example["Date"] = example["Date"].dt.strftime("%Y-%m-%d")
    example["Value (GWh)"] = (example["Value_MWh"] / 1000).round(2)

    col1, col2 = st.columns(2)
    with col1:
        st.caption("Before (MWh)")
        st.dataframe(example[["Date", "Value_MWh"]], width="stretch", hide_index=True)
    with col2:
        st.caption("After (GWh)")
        st.dataframe(example[["Date", "Value (GWh)"]], width="stretch", hide_index=True)


def page_outliers() -> None:
    section_title("📊", "Outlier treatment",
                  "Detection and correction of outliers in daily demand.")

    st.markdown(
        "No extraordinary events were associated with the outliers. "
        "For treatment, **if daily demand exceeded 1.3 times the mean, the "
        "value was replaced by the mean**. This may be due to accumulated demand "
        "records spanning multiple days or data entry errors."
    )

    df = load_sample("outliers_demanda_altos.csv")
    valor_col = next((c for c in df.columns if df[c].dtype in ("float64", "int64")), None)

    if not df.empty and valor_col:
        with st.container(border=True):
            st.markdown("##### Detected demand outliers")
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(df.head(12), width="stretch", hide_index=True)
            with col2:
                st.line_chart(df.set_index(df.columns[0])[valor_col], height=320)
    else:
        st.warning("No numeric column found for charting in the outliers file.")


def page_prophet_models() -> None:
    section_title("🔮", "Forecasting models (Prophet)",
                  "Daily demand and generation forecasting with Facebook Prophet.")

    with st.expander("ℹ️ Model considerations", expanded=True):
        st.markdown(
            "- **Prophet** was used to forecast daily demand and generation.\n"
            "- Colombian **holidays** were included in the feature engineering.\n"
            "- **80 % training / 20 % test** split.\n"
            "- **Manual cross-validation** to measure robustness and avoid overfitting.\n"
            "- Prophet decomposes the series into trend, seasonality, and special effects."
        )

    tab_demand, tab_gen = st.tabs(["⚡ Demand", "🏭 Generation"])
    with tab_demand:
        st.metric("Global R² (cross-validation)", "0.22")
        figure("demanda.png", "Demand: actual vs. predicted (cross-validation)")
    with tab_gen:
        st.metric("Global R² (cross-validation)", "0.77")
        figure("generacion.png", "Generation: actual vs. predicted (cross-validation)")


def page_ml_models() -> None:
    section_title("🤖", "Regression models (ML) — Generation",
                  "Reproducible comparison of machine learning models for "
                  "generation forecasting.")

    st.markdown(
        "Complementary approach to Prophet: supervised regression with **temporal "
        "features** (lags of 1/7/14/30 days + calendar), evaluated on a temporal "
        "test set (last 20 % of the history)."
    )

    metrics = load_result_csv("metricas_generacion_ml.csv")
    if not metrics.empty:
        best = metrics.sort_values("R2", ascending=False).iloc[0]
        st.markdown("##### Best model")
        c1, c2, c3 = st.columns(3)
        c1.metric("Model", str(best["Modelo"]))
        c2.metric("R²", f"{best['R2']:.3f}")
        c3.metric("MAE", f"{best['MAE']:.2f} GWh")

        st.markdown("##### Model comparison")
        st.dataframe(
            metrics.sort_values("R2", ascending=False).style.format(
                {"R2": "{:.3f}", "MAE": "{:.2f}", "RMSE": "{:.2f}"}
            ).background_gradient(subset=["R2"], cmap="Greens"),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Run `notebooks/modelos_generacion_ml.ipynb` to generate the metrics.")

    figure("generacion_ml_real_vs_pred.png", "Generation: actual vs. predicted (best model)")


def page_model_evaluation() -> None:
    section_title("📑", "Model evaluation",
                  "Critical assessment of the analytical use of each Prophet model.")

    col_dem, col_gen = st.columns(2)
    with col_dem:
        with st.container(border=True):
            st.markdown("### ⚡ Demand")
            st.success("Suitable for exploratory analysis, trend, and baseline scenarios.")
            st.markdown(
                "**Effectiveness**\n"
                "- Acceptable performance after cleaning outliers: R² > 0.21, low "
                "relative errors (MAPE/SMAPE < 8 %) and reasonable absolute errors.\n"
                "- Useful for projections and planning; should be complemented with "
                "exogenous variables for greater reliability.\n\n"
                "**Limitations**\n"
                "- Short history: long-term patterns underrepresented.\n"
                "- Sudden future changes may not be fully anticipated."
            )
    with col_gen:
        with st.container(border=True):
            st.markdown("### 🏭 Generation")
            st.success("Highly robust and recommended for predictive and comparative analysis.")
            st.markdown(
                "**Effectiveness**\n"
                "- High cross-validated R² (~0.77), low error dispersion, and excellent "
                "actual vs. predicted visual fit.\n"
                "- Reliable for long-term reports and energy policy decisions.\n\n"
                "**Limitations**\n"
                "- Depends on the future behaving like the past. For structural changes, "
                "additional regressors should be added."
            )

    st.markdown("##### Summary")
    summary = pd.DataFrame({
        "Variable": ["Demand", "Generation"],
        "Analytical use": ["Exploration, trend", "Prediction and analysis"],
        "Robustness": ["Acceptable", "High"],
        "Recommendation level": ["Good", "Very good"],
    })
    st.dataframe(summary, width="stretch", hide_index=True)

    st.caption(
        "Sources: [1] Prophet: Automatic Forecasting Procedure · "
        "[2] Time Series Forecasting using Facebook Prophet"
    )


def page_comparison() -> None:
    section_title("📈", "Comparison and conclusions",
                  "Demand vs. generation and electrical system projections.")

    figure("comparacion.png", "Demand vs. Generation")

    st.markdown("### Validation of conclusions")
    st.markdown(
        "- According to **UPME**, demand will grow on average **2.38 % annually** until "
        "2038, which could lead to a **structural deficit from 2027** without new "
        "investments in generation.\n"
        "- Colombia should add **3,000–4,000 MW** of firm capacity per year, but "
        "only reaches about **30 %** of that goal.\n"
        "- **Solar** capacity in operation has grown by up to **187 %** in three years.\n"
        "- Over **4,500 MW** have already been awarded in non-conventional sources (FNCER).\n"
        "- Official goal: **double** renewable capacity by 2030 and reach at least "
        "**6 GW** by 2026.\n"
        "- Bottlenecks persist: environmental licensing, prior consultations, and "
        "transmission limitations."
    )

    with st.expander("Renewable growth variation factors"):
        st.markdown(
            "- Regulatory and administrative agility.\n"
            "- Investment in transmission and storage.\n"
            "- Adoption of distributed generation (solar self-generation).\n"
            "- Attractiveness of power purchase agreements (PPA).\n"
            "- Incentives for self-generation and energy communities.\n"
            "- Surplus management (batteries) to address the generation–consumption gap."
        )

    with st.expander("Projections report (2025)"):
        st.markdown(
            "Demand will increase ~2.38 % annually, putting pressure on infrastructure and "
            "requiring investments to avoid a deficit from 2027. Although renewable capacity "
            "is growing fast and there are doubling targets for 2030, the actual pace depends "
            "on regulatory, infrastructure, and financial factors. With over 4,500 MW awarded "
            "and 14 % of the energy mix already renewable, sustaining the system will require "
            "continued investment, avoiding bottlenecks, and strengthening storage and "
            "long-term contracts. Therefore, projection models must account for the "
            "uncertainty of renewable growth."
        )


def page_sources() -> None:
    section_title("📚", "Sources", "Official references and sector analysis.")
    sources = {
        "UPME": "Official demand and generation projections.",
        "Atlas Renewable Energy": "Energy sector perspectives and trends.",
        "El Colombiano": "Analysis on growth and deficit in the electrical sector.",
        "Caracol Radio": "Report on projected energy deficit for 2027.",
        "SITTCA": "Renewable momentum analysis and recent figures.",
        "DNP": "Renewable energy reports and projections.",
        "El Universal": "Risks of energy shortfall for 2026.",
        "SER Colombia": "Expansion of non-conventional sources (FNCER).",
        "Invest in Colombia": "Renewable project awards and growth.",
        "SEI": "Studies on solar, wind, and energy communities.",
        "Climatetracker Latinoamérica": "Challenges and opportunities for renewables.",
    }
    for source, desc in sources.items():
        st.markdown(f"- **{source}** — {desc}")


# --------------------------------------------------------------------------- #
# Navigation
# --------------------------------------------------------------------------- #
PAGES = {
    "🏠 Home": page_home,
    "📂 Raw data": page_data,
    "🔧 Transformations": page_transformations,
    "📊 Outlier treatment": page_outliers,
    "🔮 Models (Prophet)": page_prophet_models,
    "🤖 ML Models (generation)": page_ml_models,
    "📑 Model evaluation": page_model_evaluation,
    "📈 Comparison and conclusions": page_comparison,
    "📚 Sources": page_sources,
}

with st.sidebar:
    st.title("⚡ Energy Colombia")
    st.caption("Electrical system analysis and forecasting")
    st.divider()
    selection = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")
    st.divider()
    st.link_button("⭐ View on GitHub", GITHUB_URL, width="stretch")
    st.caption("Data analysis project · Python · Prophet · Streamlit")

PAGES[selection]()
