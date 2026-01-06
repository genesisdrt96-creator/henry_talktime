import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz  # Thư viện xử lý múi giờ

# --- 1. CẤU HÌNH TRANG & UI LUXURY ---
st.set_page_config(page_title="Dream Talent - Henry Master Hub", layout="wide")

# XỬ LÝ MÚI GIỜ MIỀN ĐÔNG HOA KỲ (EST/EDT)
tz_US_Eastern = pytz.timezone('US/Eastern')
now = datetime.now(tz_US_Eastern)
static_time = now.strftime("%m/%d/%Y | %H:%M")
file_date = now.strftime("%m-%d-%Y")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #050E3C 0%, #1e3a8a 100%);
        color: white; padding: 15px; border-radius: 12px;
        text-align: center; font-weight: 800; font-size: 22px; margin-bottom: 15px;
    }
    .metric-container { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 15px; }
    .metric-box {
        background-color: white; padding: 5px 10px; border-radius: 10px; flex: 1; text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;
    }
    .metric-title { color: #000000; font-size: 11px; font-weight: 700; margin-bottom: -2px; text-transform: uppercase; }
    .metric-value { color: #000000; font-size: 24px; font-weight: 900; line-height: 1.2; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        border: none !important; color: #000000 !important;
        font-weight: 800 !important; font-size: 14px !important; padding: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
STAFF_CONFIG = {
    "Andres Nguyen": "GOLD", "Charlie Nguyen": "GOLD", "Amy Tran": "GOLD",
    "Alan Nguyen": "GOLD", "Rio Le": "GOLD", "Thierry Phung": "SILVER",
    "Ivan Huynh": "SILVER", "David Vo": "SILVER", "Kathy Bui": "BRONZE",
    "Jayce Mai": "BRONZE", "Jolie Nguyen": "BRONZE", "William Nguyen": "SILVER",
    "Polo Nguyen": "Associated", "Louisa Ngo": "Associated", "Winnie Pham": "Probation",
    "Avis Nguyen": "Probation", "Phoenix Nguyen": "Probation", "Ginny Nguyen": "Probation"
}
STAFF_LIST = list(STAFF_CONFIG.keys())
LEVEL_TARGETS = {"GOLD": 9000, "SILVER": 9000, "BRONZE": 9000, "Associated": 9000, "Probation": 10800}
LEVEL_COLORS = {"GOLD": "#FEF3C7", "SILVER": "#F1F5F9", "BRONZE": "#FFEDD5", "Associated": "#DBEAFE", "Probation": "#DCFCE7"}

def to_seconds(s):
    if pd.isna(s) or str(s).lower() == 'in progress' or s == '-': return 0
    try:
        parts = str(s).strip().split(':')
        if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
        return 0
    except: return 0

def format_time(seconds):
    if seconds <= 0: return "00:00:00"
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# --- 3. SESSION STATE ---
if 'input_df' not in st.session_state:
    st.session_state.input_df = pd.DataFrame({
        "Sales Name": STAFF_LIST, "Chốt $": 0.0, "Xin OFF": False, "Giảm số P": 0.0
    }).set_index("Sales Name")

def update_input():
    if "editor_v81" in st.session_state:
        for row_idx, changes in st.session_state["editor_v81"]["edited_rows"].items():
            for k, v in changes.items():
                st.session_state.input_df.iloc[row_idx, st.session_state.input_df.columns.get_loc(k)] = v

# --- 4. SIDEBAR ---
st.sidebar.markdown("# 💎 Master Dashboard")
uploaded_file = st.sidebar.file_uploader("📂 1. Tải file RingCentral", type=["csv"])
csv_input_file = st.sidebar.file_uploader("📂 2. Tải file Sales (CSV)", type=["csv"])

if csv_input_file:
    try:
        df_csv = pd.read_csv(csv_input_file)
        df_csv.columns = df_csv.columns.str.strip()
        df_csv = df_csv.set_index("Sales Name")
        st.session_state.input_df.update(df_csv)
        st.sidebar.success("✅ Đã nạp dữ liệu từ CSV!")
    except Exception as e:
        st.sidebar.error(f"Lỗi file CSV: {e}")

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
    df_raw.columns = df_raw.columns.str.strip()
    df_raw['Ext_Name'] = df_raw['Extension'].str.split(' - ', n=1).str[1].fillna("Unknown")
    df_raw['Sec'] = df_raw['Duration'].apply(to_seconds)
    
    active_in_file = df_raw['Ext_Name'].unique()
    active_staff = [name for name in STAFF_LIST if name in active_in_file]
    
    stats = df_raw[df_raw['Ext_Name'].isin(active_staff)].groupby('Ext_Name').agg(
        Tong_Cuoc_Goi=('Action', 'count'), Actual_Sec=('Sec', 'sum'),
        Int_5p=('Sec', lambda x: (x >= 300).sum()), 
        Int_10p=('Sec', lambda x: (x >= 600).sum()), 
        Int_30p=('Sec', lambda x: (x >= 1800).sum())
    ).reindex(active_staff).fillna(0)

    current_input_display = st.session_state.input_df.loc[active_staff]

    # --- 5. NHẬP LIỆU ---
    st.subheader("📝 1. BẢNG NHẬP DOANH SỐ & ĐIỀU CHỈNH")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.data_editor(current_input_display, use_container_width=True, key="editor_v81", on_change=update_input, height=((len(active_staff)*35)+40))
    
    final_df = pd.concat([current_input_display, stats], axis=1).fillna(0).reset_index()
    final_df.rename(columns={'index': 'Sales Name'}, inplace=True)

    # --- 6. TÍNH TOÁN ---
    def calculate_metrics(row):
        name = row['Sales Name']
        lvl = STAFF_CONFIG.get(name, "Probation")
        target_orig = LEVEL_TARGETS.get(lvl, 10800) 
        actual = row['Actual_Sec']
        if row['Xin OFF']: return pd.Series([lvl, target_orig, actual, 0, 0.0, "OFF"])
        sales = row['Chốt $']
        bonus = 1800 if 300 <= sales < 500 else (2700 if 500 <= sales < 1000 else (5400 if 1000 <= sales < 2000 else 0))
        is_done = sales >= 2000
        total_red = (target_orig if is_done else (bonus + row['Giảm số P'] * 60))
        target_final = max(0, target_orig - total_red)
        pct = 100.0 if (is_done or target_final <= 0) else (actual / target_final * 100)
        return pd.Series([lvl, target_final, actual, total_red, round(float(pct), 1), "GOOD JOB" if pct >= 100.0 or is_done else "Come on!"])

    final_df[['🏅 LVL', 'target_val', 'actual_val', 'red_val', 'pct_val', '📊 RESULT']] = final_df.apply(calculate_metrics, axis=1)
    final_df = final_df.sort_values(by='pct_val', ascending=False).reset_index(drop=True)

    # --- 7. UI HEADER HIỂN THỊ GIỜ MỸ ---
    st.markdown(f'<div class="main-header">🏆 WORKING RESULTS STATISTICS | {static_time} (EST)</div>', unsafe_allow_html=True)
    
    t_p, t_t, t_c = int(final_df['Chốt $'].sum()), format_time(final_df['Actual_Sec'].sum()), int(final_df['Tong_Cuoc_Goi'].sum())
    st.markdown(f"""<div class="metric-container">
        <div class="metric-box"><div class="metric-title">💰 Total Premium</div><div class="metric-value">${t_p:,}</div></div>
        <div class="metric-box"><div class="metric-title">⏱️ Total Talktime</div><div class="metric-value">{t_t}</div></div>
        <div class="metric-box"><div class="metric-title">📞 Total Calls</div><div class="metric-value">{t_c:,}</div></div>
    </div>""", unsafe_allow_html=True)

    # --- 8. BẢNG HIỂN THỊ ---
    disp_df = pd.DataFrame()
    disp_df['👤 SALES'] = final_df['Sales Name']; disp_df['🏅 LVL'] = final_df['🏅 LVL']
    disp_df['💵 CHỐT $'] = final_df['Chốt $']; disp_df['🎯 GOAL'] = final_df['target_val'].apply(format_time)
    disp_df['⏱️ CALL'] = final_df['actual_val'].apply(format_time)
    disp_df['📉 GIẢM TALKTIME'] = final_df['red_val'].apply(lambda x: "🏆 DONE" if x >= 9000 else f"{int(x//60)}p")
    disp_df['% HOÀN THÀNH'] = final_df['pct_val']
    disp_df['🔥 5P'] = final_df['Int_5p'].astype(int); disp_df['🔥 10P'] = final_df['Int_10p'].astype(int)
    disp_df['🔥 30P'] = final_df['Int_30p'].astype(int); disp_df['📊 RESULT'] = final_df['📊 RESULT']

    def apply_row_styles(row):
        styles = [''] * len(row); idx = row.name 
        r = final_df.iloc[idx]
        if r['🏅 LVL'] in LEVEL_COLORS: styles[1] = f'background-color: {LEVEL_COLORS[r["🏅 LVL"]]};'
        if r['Chốt $'] > 0: styles[2] = 'background-color: #fee2e2; color: #b91c1c; font-weight: 800;'
        if r['actual_val'] >= r['target_val'] and r['target_val'] > 0:
            styles[4] = 'background-color: #dcfce7; color: #15803d; font-weight: 800;'
        if r['pct_val'] >= 100: styles[6] = 'background-color: #fee2e2; color: #b91c1c; font-weight: 800;'
        res = r['📊 RESULT']
        if res == "GOOD JOB": styles[10] = 'background-color: #dbeafe; color: #1e40af; font-weight: 800;'
        elif res != "OFF": styles[10] = 'background-color: #fee2e2; color: #b91c1c; font-weight: 800;'
        return styles

    st.dataframe(disp_df.style.apply(apply_row_styles, axis=1), use_container_width=True, hide_index=True, height=(len(active_staff)*35+50),
        column_config={"💵 CHỐT $": st.column_config.NumberColumn(format="$%d"), "% HOÀN THÀNH": st.column_config.NumberColumn(format="%.1f%%")})

    fig = px.bar(final_df[final_df['📊 RESULT'] != "OFF"], x='Sales Name', y='pct_val', color='pct_val', color_continuous_scale='Blues', text_auto='.1f', height=350)
    fig.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig, use_container_width=True)
    
    st.sidebar.download_button("📥 Export CSV", disp_df.to_csv(index=False).encode('utf-8-sig'), f"Report_{file_date}.csv")
else:
    st.info("👋 Chào Team Henry! Hãy tải file RingCentral nhé.")
