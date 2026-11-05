import datetime
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="BEI Donchian 15M Screener", page_icon="📈", layout="wide"
)

st.title("📈 Screener Pantulan Donchian Channel 15m (BEI)")
st.caption(
    "Aplikasi otomatis pendeteksi potensi pantulan harga saham BEI pada timeframe 15 Menit."
)

# Sidebar - Parameter Input
st.sidebar.header("⚙️ Parameter Screener")

donchian_period = st.sidebar.number_input(
    "Periode Donchian Channel", min_value=5, max_value=50, value=20
)
min_tx_val = (
    st.sidebar.number_input(
        "Min. Transaksi Harian (Rp Juta)", min_value=0, value=500
    )
    * 1_000_000
)

# List ticker saham populer BEI (bisa ditambah sesuai kebutuhan)
DEFAULT_TICKERS = [
    "BBCA.JK",
    "BBRI.JK",
    "BMRI.JK",
    "BBNI.JK",
    "TLKM.JK",
    "ASII.JK",
    "UNTR.JK",
    "AMRT.JK",
    "ICBP.JK",
    "GOTO.JK",
    "BRMS.JK",
    "BRPT.JK",
    "ADRO.JK",
    "PTBA.JK",
    "PGAS.JK",
    "ANTM.JK",
    "MEDC.JK",
    "MDKA.JK",
    "CPIN.JK",
    "JPFA.JK",
]

tickers_input = st.sidebar.text_area(
    "Daftar Ticker (Pisahkan dengan koma/baris baru)",
    value="\n".join(DEFAULT_TICKERS),
    height=200,
)

tickers_list = [
    t.strip().upper()
    for t in tickers_input.replace(",", "\n").split("\n")
    if t.strip()
]

# Tombol Scan
scan_button = st.sidebar.button("🚀 MULAI SCAN", type="primary")


def analyze_stock(ticker, window=20):
    """Mengambil data 15m & menghitung Donchian Channel serta sinyal pantulan."""
    try:
        # Mengambil data 15m untuk 60 hari terakhir (limit maksimum Yahoo Finance)
        df = yf.download(
            ticker, period="5d", interval="15m", progress=False, multi_level_index=False
        )

        if df.empty or len(df) < window:
            return None

        # Hitung Donchian Channel (menggunakan shift agar tidak repainting)
        df["Donchian_Low"] = df["Low"].shift(1).rolling(window=window).min()
        df["Donchian_High"] = df["High"].shift(1).rolling(window=window).max()

        last_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]

        current_close = float(last_candle["Close"])
        current_open = float(last_candle["Open"])
        current_low = float(last_candle["Low"])
        current_vol = float(last_candle["Volume"])
        donchian_low_val = float(last_candle["Donchian_Low"])

        # Nilai transaksi perkiraan candle ini
        tx_val = current_close * current_vol

        # Deteksi Sinyal
        signal = "Tidak Ada"

        # Kriteria 1: Low candle sebelumnya/sekarang menyentuh/mendekati Donchian Low
        near_donchian = current_low <= donchian_low_val * 1.005  # Toleransi 0.5%

        # Kriteria 2: Candle hijau (Pantulan pertama)
        is_bullish = current_close > current_open

        if near_donchian and is_bullish:
            signal = "🔥 Pantulan (Buy Candidate)"
        elif near_donchian:
            signal = "👀 Pantau (Uji Support)"

        return {
            "Kode": ticker.replace(".JK", ""),
            "Harga": f"Rp {current_close:,.0f}",
            "Donchian Low": f"Rp {donchian_low_val:,.0f}",
            "Volume": f"{current_vol:,.0f}",
            "Nilai Tx (Est)": f"Rp {tx_val/1_000_000:,.1f} Jt",
            "Sinyal": signal,
            "_raw_tx": tx_val,
            "_raw_signal": signal,
        }
    except Exception:
        return None


# Tampilan utama
if scan_button:
    st.info(f"Memindai {len(tickers_list)} saham pada interval 15 Menit...")
    progress_bar = st.progress(0)

    results = []
    for i, ticker in enumerate(tickers_list):
        data = analyze_stock(ticker, window=donchian_period)
        if data and data["_raw_tx"] >= min_tx_val:
            results.append(data)
        progress_bar.progress((i + 1) / len(tickers_list))

    if results:
        res_df = pd.DataFrame(results)

        # Filter tampilan berdasarkan sinyal menarik dulu
        res_df = res_df.drop(columns=["_raw_tx"])

        st.subheader("📌 Hasil Pemindaian")
        st.dataframe(res_df, use_container_width=True)
    else:
        st.warning("Tidak ada saham yang memenuhi kriteria kustom/minimal transaksi saat ini.")
else:
    st.write(
        "Tekan tombol **MULAI SCAN** di sidebar sebelah kiri untuk mendeteksi saham."
    )
