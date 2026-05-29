"""Sargon — AI Investment Advisor  (Streamlit frontend)"""

import os
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Sargon Investment Advisor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar nav ───────────────────────────────────────────────────────────────

st.sidebar.title("Sargon")
st.sidebar.caption("AI-Powered Investment Advisor")
page = st.sidebar.radio(
    "Navigate",
    ["Risk Profiler", "Portfolio Optimizer", "Tax Optimizer", "Portfolio Rebalancer"],
)
st.sidebar.markdown("---")
st.sidebar.info(f"API: `{API_URL}`")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _post(endpoint: str, payload: dict) -> dict | None:
    try:
        r = requests.post(f"{API_URL}/{endpoint}", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the Sargon API. Make sure the backend is running.")
    except requests.exceptions.HTTPError as exc:
        detail = exc.response.json().get("detail", str(exc))
        st.error(f"API error: {detail}")
    return None


def _get(endpoint: str) -> dict | None:
    try:
        r = requests.get(f"{API_URL}/{endpoint}", timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the Sargon API. Make sure the backend is running.")
    except requests.exceptions.HTTPError as exc:
        st.error(f"API error: {exc}")
    return None


# ── Page: Risk Profiler ───────────────────────────────────────────────────────

if page == "Risk Profiler":
    st.title("Risk Profiler")
    st.write("Answer the questions below to discover your investor risk profile.")

    data = _get("risk-questions")
    if data is None:
        st.stop()

    questions = data["questions"]
    answers: dict[str, int] = {}
    with st.form("risk_form"):
        for q in questions:
            options = q["options"]
            labels = [o["label"] for o in options]
            chosen = st.radio(q["question"], labels, key=q["id"])
            chosen_value = next(o["value"] for o in options if o["label"] == chosen)
            answers[q["id"]] = chosen_value

        submitted = st.form_submit_button("Get My Risk Profile", type="primary")

    if submitted:
        with st.spinner("Analyzing your profile…"):
            result = _post("risk-profile", {"answers": answers})
        if result:
            cat = result["category"].capitalize()
            col1, col2 = st.columns([1, 2])
            with col1:
                color = {"Conservative": "blue", "Moderate": "orange", "Aggressive": "red"}.get(cat, "green")
                st.metric("Risk Category", cat)
                st.metric("Score", result["score"])
                st.write(result["description"])
            with col2:
                alloc = result["suggested_allocation"]
                fig = px.pie(
                    names=list(alloc.keys()),
                    values=list(alloc.values()),
                    title="Suggested Asset Allocation",
                    hole=0.4,
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True)


# ── Page: Portfolio Optimizer ─────────────────────────────────────────────────

elif page == "Portfolio Optimizer":
    st.title("Portfolio Optimizer")
    st.write(
        "Enter stock/ETF tickers and we'll find the **maximum Sharpe-ratio** portfolio "
        "using Modern Portfolio Theory."
    )

    with st.form("optimizer_form"):
        raw = st.text_input(
            "Tickers (comma-separated)",
            value="SPY, QQQ, GLD, TLT, VNQ",
            help="Use Yahoo Finance symbols, e.g. AAPL, BTC-USD, SPY",
        )
        rf = st.slider("Risk-Free Rate (%)", 0.0, 10.0, 5.0, 0.25) / 100
        submitted = st.form_submit_button("Optimize Portfolio", type="primary")

    if submitted:
        tickers = [t.strip().upper() for t in raw.split(",") if t.strip()]
        if len(tickers) < 2:
            st.warning("Please enter at least 2 tickers.")
        else:
            with st.spinner(f"Fetching 2 years of data for {tickers} and optimizing…"):
                result = _post("optimize", {"tickers": tickers, "risk_free_rate": rf})
            if result:
                col1, col2, col3 = st.columns(3)
                col1.metric("Expected Annual Return", f"{result['expected_return']:.1f}%")
                col2.metric("Annual Volatility", f"{result['volatility']:.1f}%")
                col3.metric("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}")

                # Weights chart
                weights = result["weights"]
                fig_w = px.bar(
                    x=list(weights.keys()),
                    y=[v * 100 for v in weights.values()],
                    labels={"x": "Ticker", "y": "Weight (%)"},
                    title="Optimal Portfolio Weights",
                    color=list(weights.keys()),
                )
                fig_w.update_layout(showlegend=False)
                st.plotly_chart(fig_w, use_container_width=True)

                # Efficient frontier
                ef = result.get("efficient_frontier", [])
                if ef:
                    df_ef = pd.DataFrame(ef)
                    fig_ef = go.Figure()
                    fig_ef.add_trace(
                        go.Scatter(
                            x=df_ef["volatility"],
                            y=df_ef["return"],
                            mode="lines+markers",
                            name="Efficient Frontier",
                            line=dict(color="royalblue", width=2),
                        )
                    )
                    fig_ef.add_trace(
                        go.Scatter(
                            x=[result["volatility"]],
                            y=[result["expected_return"]],
                            mode="markers",
                            marker=dict(color="red", size=12, symbol="star"),
                            name="Max Sharpe Portfolio",
                        )
                    )
                    fig_ef.update_layout(
                        title="Efficient Frontier",
                        xaxis_title="Volatility (%)",
                        yaxis_title="Expected Return (%)",
                    )
                    st.plotly_chart(fig_ef, use_container_width=True)


# ── Page: Tax Optimizer ───────────────────────────────────────────────────────

elif page == "Tax Optimizer":
    st.title("Tax-Loss Harvesting")
    st.write(
        "Add your holdings below. Sargon will identify positions with harvestable losses "
        "and suggest replacement securities to maintain your exposure."
    )

    if "tax_holdings" not in st.session_state:
        st.session_state.tax_holdings = [
            {"ticker": "AAPL", "shares": 10.0, "cost_basis": 180.0, "purchase_date": date.today() - timedelta(days=90)},
            {"ticker": "TSLA", "shares": 5.0, "cost_basis": 280.0, "purchase_date": date.today() - timedelta(days=200)},
        ]

    st.subheader("Your Holdings")
    edited = st.data_editor(
        pd.DataFrame(st.session_state.tax_holdings),
        num_rows="dynamic",
        column_config={
            "ticker": st.column_config.TextColumn("Ticker", required=True),
            "shares": st.column_config.NumberColumn("Shares", min_value=0.001, format="%.4f"),
            "cost_basis": st.column_config.NumberColumn("Cost Basis / Share ($)", min_value=0.01, format="%.2f"),
            "purchase_date": st.column_config.DateColumn("Purchase Date"),
        },
        use_container_width=True,
        key="tax_editor",
    )

    if st.button("Analyze Tax-Loss Opportunities", type="primary"):
        rows = edited.to_dict("records")
        payload_holdings = [
            {
                "ticker": r["ticker"].upper(),
                "shares": float(r["shares"]),
                "cost_basis": float(r["cost_basis"]),
                "purchase_date": str(r["purchase_date"]),
            }
            for r in rows
            if r.get("ticker")
        ]
        with st.spinner("Fetching live prices and analyzing losses…"):
            result = _post("tax-optimize", {"holdings": payload_holdings})
        if result:
            suggestions = result["suggestions"]
            if not suggestions:
                st.success("No significant tax-loss harvesting opportunities found.")
            else:
                st.warning(f"Found {len(suggestions)} harvesting opportunity(ies).")
                for s in suggestions:
                    with st.expander(
                        f"{s['ticker']}  |  Loss: ${abs(s['unrealized_loss']):,.2f} ({s['loss_pct']:.1f}%)"
                    ):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Current Price", f"${s['current_price']:.2f}")
                        c2.metric("Cost Basis", f"${s['cost_basis']:.2f}")
                        c3.metric("Unrealized Loss", f"${s['unrealized_loss']:,.2f}")
                        st.write(f"**Action:** {s['action']}")
                        if s["replacement_tickers"]:
                            st.write(f"**Replacement suggestions:** {', '.join(s['replacement_tickers'])}")
                        if s["wash_sale_warning"]:
                            st.warning(
                                "Wash-sale risk: this position was purchased less than 30 days ago. "
                                "Selling and rebuying the same security within 30 days disallows the loss."
                            )


# ── Page: Portfolio Rebalancer ────────────────────────────────────────────────

elif page == "Portfolio Rebalancer":
    st.title("Portfolio Rebalancer")
    st.write("Enter your current holdings and target allocation to see rebalancing trades.")

    col_hold, col_target = st.columns(2)

    with col_hold:
        st.subheader("Current Holdings")
        if "rb_holdings" not in st.session_state:
            st.session_state.rb_holdings = pd.DataFrame(
                [
                    {"ticker": "SPY", "shares": 20.0},
                    {"ticker": "QQQ", "shares": 15.0},
                    {"ticker": "GLD", "shares": 10.0},
                    {"ticker": "TLT", "shares": 30.0},
                ]
            )
        hold_df = st.data_editor(
            st.session_state.rb_holdings,
            num_rows="dynamic",
            column_config={
                "ticker": st.column_config.TextColumn("Ticker", required=True),
                "shares": st.column_config.NumberColumn("Shares", min_value=0.001, format="%.4f"),
            },
            use_container_width=True,
            key="rb_hold_editor",
        )

    with col_target:
        st.subheader("Target Allocation (%)")
        if "rb_target" not in st.session_state:
            st.session_state.rb_target = pd.DataFrame(
                [
                    {"ticker": "SPY", "target_pct": 40.0},
                    {"ticker": "QQQ", "target_pct": 25.0},
                    {"ticker": "GLD", "target_pct": 15.0},
                    {"ticker": "TLT", "target_pct": 20.0},
                ]
            )
        target_df = st.data_editor(
            st.session_state.rb_target,
            num_rows="dynamic",
            column_config={
                "ticker": st.column_config.TextColumn("Ticker", required=True),
                "target_pct": st.column_config.NumberColumn("Target %", min_value=0.0, max_value=100.0, format="%.1f"),
            },
            use_container_width=True,
            key="rb_target_editor",
        )
        total_pct = target_df["target_pct"].sum()
        if abs(total_pct - 100) > 0.5:
            st.error(f"Allocations sum to {total_pct:.1f}% — must equal 100%.")

    threshold = st.slider("Rebalance threshold (% drift to trigger)", 1.0, 15.0, 5.0, 0.5)

    if st.button("Calculate Rebalancing Trades", type="primary"):
        holdings_dict = {
            r["ticker"].upper(): float(r["shares"])
            for _, r in hold_df.iterrows()
            if r.get("ticker")
        }
        target_dict = {
            r["ticker"].upper(): float(r["target_pct"])
            for _, r in target_df.iterrows()
            if r.get("ticker")
        }
        payload = {
            "holdings": holdings_dict,
            "target_allocation": target_dict,
            "threshold": threshold,
        }
        with st.spinner("Fetching live prices and calculating trades…"):
            result = _post("rebalance", payload)
        if result:
            actions = result["actions"]
            if not actions:
                st.info("No rebalancing data returned.")
            else:
                df = pd.DataFrame(actions)

                # Color-coded summary
                def _color_action(val):
                    colors = {"BUY": "background-color:#d4edda", "SELL": "background-color:#f8d7da", "HOLD": ""}
                    return colors.get(val, "")

                styled = df.style.applymap(_color_action, subset=["action"])
                st.dataframe(styled, use_container_width=True, hide_index=True)

                # Drift bar chart
                fig = go.Figure()
                colors = ["green" if a["action"] == "BUY" else "red" if a["action"] == "SELL" else "gray"
                          for a in actions]
                fig.add_trace(
                    go.Bar(
                        x=[a["ticker"] for a in actions],
                        y=[a["drift"] for a in actions],
                        marker_color=colors,
                        name="Drift (%)",
                    )
                )
                fig.update_layout(
                    title="Portfolio Drift from Target",
                    xaxis_title="Ticker",
                    yaxis_title="Drift (%)",
                    shapes=[
                        dict(type="line", y0=threshold, y1=threshold, x0=-0.5, x1=len(actions) - 0.5,
                             line=dict(color="orange", dash="dash")),
                        dict(type="line", y0=-threshold, y1=-threshold, x0=-0.5, x1=len(actions) - 0.5,
                             line=dict(color="orange", dash="dash")),
                    ],
                )
                st.plotly_chart(fig, use_container_width=True)
