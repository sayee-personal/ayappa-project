import io
import pandas as pd
import streamlit as st
import scipy.optimize as optimize
from datetime import datetime
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from google.cloud import storage

# ==========================================
# CONFIGURATION
# ==========================================
GCP_BUCKET_NAME = "my-bond-screener-bucket"

st.set_page_config(layout="wide", page_title="⚡ QUANT-AI Bond Terminal", page_icon="⚡")

# ==========================================
# 1. CORE DATA CALCULATIONS & CONNECTIONS
# ==========================================

def calculate_ytm(price, face_value, coupon_rate, years_to_maturity, frequency=1):
    if years_to_maturity <= 0: 
        return 0.0
    coupon_payment = face_value * (coupon_rate / 100)
    
    def bond_price_equation(y):
        periods = int(years_to_maturity * frequency)
        if periods == 0: 
            periods = 1
        pv = sum([(coupon_payment / frequency) / ((1 + y / frequency) ** t) for t in range(1, periods + 1)])
        pv += face_value / ((1 + y / frequency) ** periods)
        return pv - price
        
    try:
        return round(optimize.newton(bond_price_equation, 0.08) * 100, 2)
    except:
        return None

def fetch_single_bond(isin, ltp, volume):
    api_url = f"https://api.bondcentral.in/securities/?isin={isin}&page=1&size=10"
    try:
        res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if res.status_code == 200:
            raw_json = res.json()
            if 'data' in raw_json and len(raw_json['data']) > 0:
                bond_info = raw_json['data'][0].get('data', {})
                raw_ratings = bond_info.get('ratings', [])
                rating = raw_ratings[0].get('cra_rating', 'Unrated') if raw_ratings else "Unrated"
                coupon_rate = float(bond_info.get('coupon_rate') or 0.0)
                face_value = float(bond_info.get('face_value') or 1000.0)
                maturity_text = bond_info.get('maturity_date', '').split(" ")[0]

                maturity_date = datetime.strptime(maturity_text, "%Y-%m-%d") if maturity_text else datetime.now()
                yrs_to_mat = round((maturity_date - datetime.now()).days / 365.25, 2)

                return {
                    "ISIN": isin, 
                    "Issuer": bond_info.get('issuer', 'Unknown Issuer'),
                    "Rating": rating, 
                    "Coupon (%)": coupon_rate,
                    "Maturity": maturity_date.strftime("%Y-%m-%d"), 
                    "Yrs to Mat": yrs_to_mat,
                    "LTP (₹)": ltp, 
                    "Volume": int(volume),
                    "YTM (%)": calculate_ytm(ltp, face_value, coupon_rate, yrs_to_mat)
                }
    except:
        pass
    return None

# ==========================================
# 2. INSTANT GCP BUCKET INGESTION
# ==========================================
@st.cache_data(ttl=1800) # Caches fully analyzed output for 30 minutes
def load_all_market_data():
    file_name = "latest_bhavcopy.csv"
    print(f"[DEBUG] Fetching safe file managed by cron job: {file_name}")

    # Explicitly use the storage client instead of passing string URIs to pandas
    try:
        client = storage.Client(project="fresh-geography-498007-b6")
        bucket = client.bucket(GCP_BUCKET_NAME)
        blob = bucket.blob(file_name)
        
        if not blob.exists():
            print(f"[DEBUG] Critical Fault: {file_name} not found in bucket.")
            return pd.DataFrame()
            
        csv_bytes = blob.download_as_bytes()
        df = pd.read_csv(io.BytesIO(csv_bytes), low_memory=False)
    except Exception as e:
        st.error(f"GCP Storage Read Failure via Native API. Error: {e}")
        return pd.DataFrame()

    df.columns = df.columns.str.strip()
    col_srs = next((c for c in ['SctySrs', 'SERIES'] if c in df.columns), None)
    col_isin = next((c for c in ['ISIN', 'Isin'] if c in df.columns), None)
    col_close = next((c for c in ['ClsPric', 'ClsPrc', 'CLOSE'] if c in df.columns), None)
    col_vol = next((c for c in ['TtlTradgVol', 'TotTrdQty', 'VOLUME'] if c in df.columns), None)

    bond_series = [
        'N0', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9', 'N10',
        'NA', 'NB', 'NC', 'ND', 'NE', 'NF', 'NG', 'NH', 'NI', 'NJ', 'NK', 'NL',
        'NM', 'NN', 'NO', 'NP', 'NQ', 'NR', 'NS', 'NT', 'NU', 'NV', 'NW', 'NX',
        'NY', 'NZ', 'Y0', 'Y1', 'Y2', 'Y3', 'Y4', 'Y5', 'Y6', 'Y7', 'Y8', 'Y9',
        'YA', 'YB', 'YC', 'YD', 'YE', 'YF', 'YG', 'YH', 'YI', 'YJ', 'YK', 'YL',
        'YM', 'YN', 'YO', 'YP', 'YQ', 'YR', 'YS', 'YT', 'YU', 'YV', 'YW', 'YX',
        'YY', 'YZ'
    ]
    
    if not col_srs or not col_isin or not col_close or not col_vol:
        print("[DEBUG] Alignment Error: Missing target market matrix headers.")
        return pd.DataFrame()

    bonds_df = df[df[col_srs].isin(bond_series)].copy()
    bonds_df = bonds_df[[col_isin, col_close, col_vol]]
    bonds_df.columns = ['ISIN', 'LTP', 'VOLUME']

    top_bonds = bonds_df.sort_values(by='VOLUME', ascending=False)
    screener_results = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(fetch_single_bond, row['ISIN'], row['LTP'], row['VOLUME']) for _, row in top_bonds.iterrows()]
        for future in as_completed(futures):
            result = future.result()
            if result:
                screener_results.append(result)

    return pd.DataFrame(screener_results).sort_values(by='Volume', ascending=False)

# ==========================================
# 3. UI LAYOUT
# ==========================================
st.markdown("## ⚡ QUANT-AI FIXED INCOME TERMINAL")

with st.spinner("Streaming master array from GCP Cloud Bin..."):
    master_df = load_all_market_data()

if master_df.empty:
    st.error("No active data found in the cloud workspace. Ensure local cron job has executed.")
else:
    # ------------------------------------------
    # SIDEBAR: COMPLETE MATRIX FILTERS
    # ------------------------------------------
    st.sidebar.markdown("### 🛠️ Universe Filters")
    st.sidebar.markdown("---")

    all_issuers = sorted(master_df['Issuer'].unique())
    selected_issuers = st.sidebar.multiselect("Issuer Filter Matrix", all_issuers, default=all_issuers)

    all_ratings = sorted(master_df['Rating'].unique())
    selected_ratings = st.sidebar.multiselect("Credit Horizon Filters", all_ratings, default=all_ratings)

    st.sidebar.markdown("### 🎚️ Boundary Limits")
    min_yrs, max_yrs = float(master_df['Yrs to Mat'].min()), float(master_df['Yrs to Mat'].max())
    slider_yrs = st.sidebar.slider("Maturity Window (Yrs)", min_yrs, max_yrs, (min_yrs, max_yrs))

    valid_ytm = master_df['YTM (%)'].dropna()
    min_ytm, max_ytm = float(valid_ytm.min()), float(valid_ytm.max()) if not valid_ytm.empty else (0.0, 25.0)
    slider_ytm = st.sidebar.slider("Yield Range (YTM %)", min_ytm, max_ytm, (min_ytm, max_ytm))

    min_cpn, max_cpn = float(master_df['Coupon (%)'].min()), float(master_df['Coupon (%)'].max())
    slider_cpn = st.sidebar.slider("Target Coupon Range (%)", min_cpn, max_cpn, (min_cpn, max_cpn))

    min_vol, max_vol = int(master_df['Volume'].min()), int(master_df['Volume'].max())
    slider_vol = st.sidebar.slider("Liquidity Floor (Volume)", min_vol, max_vol, (min_vol, max_vol))

    filtered_df = master_df[
        (master_df['Issuer'].isin(selected_issuers)) &
        (master_df['Rating'].isin(selected_ratings)) &
        (master_df['Yrs to Mat'].between(slider_yrs[0], slider_yrs[1])) &
        (master_df['YTM (%)'].between(slider_ytm[0], slider_ytm[1])) &
        (master_df['Coupon (%)'].between(slider_cpn[0], slider_cpn[1])) &
        (master_df['Volume'].between(slider_vol[0], slider_vol[1]))
    ]

    sorted_df = filtered_df.sort_values(by=["YTM (%)", "Volume", "Yrs to Mat"], ascending=[False, False, True])

    # ------------------------------------------
    # MAIN STAGE: INSIGHT HERO CARDS
    # ------------------------------------------
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        with st.container(border=True):
            if not sorted_df.empty:
                top_yield_row = sorted_df.iloc[0]
                st.metric("🔥 ALPHA MAX YIELD", f"{top_yield_row['YTM (%)']}%", f"{top_yield_row['ISIN']}")
            else:
                st.metric("🔥 ALPHA MAX YIELD", "0.0%", "NO DATA")
    with m_col2:
        with st.container(border=True):
            if not sorted_df.empty:
                top_vol_row = sorted_df.sort_values(by="Volume", ascending=False).iloc[0]
                st.metric("👑 LIQUIDITY KING", f"{top_vol_row['Volume']:,} Qty", f"{top_vol_row['ISIN']}")
            else:
                st.metric("👑 LIQUIDITY KING", "0", "NO DATA")
    with m_col3:
        with st.container(border=True):
            aaa_pool = sorted_df[sorted_df['Rating'].str.contains("AAA", na=False)]
            if not aaa_pool.empty:
                safe_pick = aaa_pool.iloc[0]
                st.metric("🛡️ MAX SAFETY PICK", f"{safe_pick['YTM (%)']}% YTM", f"{safe_pick['ISIN']} (AAA)")
            else:
                st.metric("🛡️ MAX SAFETY PICK", "N/A", "NO ELIGIBLE BONDS")
    with m_col4:
        with st.container(border=True):
            st.metric("📊 RADAR COVERAGE", f"{len(sorted_df)} Selected", f"Out of {len(master_df)} In Universe")

    # ------------------------------------------
    # MAIN DISPLAY ARCHITECTURE
    # ------------------------------------------
    tab1, tab2 = st.tabs(["📈 Market Analytics & Curve Topology", "🔍 Full Asset Screener"])

    with tab1:
        st.markdown("### Top 10 Liquid In-Market Issues")
        st.dataframe(master_df.head(10), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### Volumetric Macro Yield Curve (Top 30 Liquidity Profiling)")
        plot_df = master_df.head(30).dropna(subset=['YTM (%)'])
        if not plot_df.empty:
            fig = px.scatter(
                plot_df, x="Yrs to Mat", y="YTM (%)", size="Volume", color="Rating",
                hover_name="ISIN", hover_data=["Issuer", "Coupon (%)", "Rating", "YTM (%)", "Volume"],
                template="plotly_white", height=500,
                color_discrete_sequence=px.colors.qualitative.Prism
            )

            fig.update_layout(
                font_family="Inter, sans-serif",
                xaxis=dict(title="Years to Maturity Profile", showgrid=True, gridcolor='#EFEFEF'),
                yaxis=dict(title="Yield to Maturity (%)", showgrid=True, gridcolor='#EFEFEF')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insufficient active vectors to display market shape.")

    with tab2:
        st.markdown("### Full Macro Screener Matrix")
        st.markdown("Rank Execution Order: **Yield Premium** -> **Liquidity Volume** -> **Short Maturity Priority**.")
        st.dataframe(
            sorted_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Volume": st.column_config.NumberColumn("Volume", format="%d"),
                "LTP (₹)": st.column_config.NumberColumn("LTP (₹)", format="%.2f"),
                "YTM (%)": st.column_config.NumberColumn("YTM (%)", format="%.2f%%"),
                "Coupon (%)": st.column_config.NumberColumn("Coupon (%)", format="%.2f%%"),
            }
        )