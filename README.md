# SOLUSDT Signal Bot

Streamlit dashboard for SOLUSDT Binance Futures market data, technical signals, historical paper simulation, and forward paper trading. Real order execution is disabled.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Open [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
2. Select `fajarprie021/SOLUSDT_SIGNAL_BOT`.
3. Set the main file to `app.py` and deploy.
4. Streamlit Cloud installs dependencies from `requirements.txt`.

The app reads public Binance Futures klines and does not require API keys. The SQLite paper-trading state is local to the running app instance and may reset when the deployment restarts.
