
import streamlit as st

st.set_page_config(
    page_title="Dashboard Test",
    layout="wide"
)

st.title("SOLUSDT AGENT DESK")

st.success(
    "STREAMLIT BERHASIL MENAMPILKAN DASHBOARD"
)

st.metric(
    "Virtual Balance",
    "5,000 USDT"
)

st.subheader("EMA Configuration")

col1, col2 = st.columns(2)

with col1:
    st.number_input(
        "EMA Fast",
        min_value=2,
        value=9
    )

with col2:
    st.number_input(
        "EMA Slow",
        min_value=3,
        value=21
    )

st.info(
    "Dashboard test berhasil dijalankan."
)
