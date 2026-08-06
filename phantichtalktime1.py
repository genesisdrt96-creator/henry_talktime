import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import os, glob, re

APP_VERSION = "2026.08.03-gsheet-live"  # đổi khi deploy — kiểm tra dòng này trên sidebar web

# --- 1. CẤU HÌNH TRANG & UI LUXURY ---
st.set_page_config(page_title="Dream Talent - Henry Master Hub", layout="wide")

# XỬ LÝ MÚI GIỜ MIỀN ĐÔNG HOA KỲ (EST/EDT)
tz_US_Eastern = pytz.timezone('US/Eastern')
now = datetime.now(tz_US_Eastern)
static_time = now.strftime("%m/%d/%Y | %H:%M")
file_date = now.strftime("%m-%d-%Y")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    html, body, .stApp, [data-testid="stAppViewContainer"], [class*="css"] {
        font-family: 'Inter','Segoe UI',Roboto,Arial,sans-serif !important;
        font-weight: 600 !important;
    }
    .stApp { background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #050E3C 0%, #17297a 100%);
        color: white; padding: 16px; border-radius: 12px;
        text-align: center; font-weight: 800; font-size: 31px; margin-bottom: 15px;
        letter-spacing: 0.3px;
    }
    /* ===== KPI CARDS ===== */
    .kpi-row { display: flex; gap: 14px; margin: 4px 0 18px 0; flex-wrap: wrap; }
    .kpi-card {
        flex: 1; min-width: 168px; text-align: center;
        background: #FFFFFF;
        border-radius: 18px; padding: 18px 16px;
        box-shadow: 0 6px 18px rgba(30,58,138,0.07);
        border: 1px solid #E6ECF5;
    }
    .kpi-ico {
        width:48px; height:48px; border-radius:14px; display:flex;
        align-items:center; justify-content:center; font-size:29px; margin:0 auto 10px auto;
    }
    .kpi-label { font-size:18px; font-weight:800; letter-spacing:.5px; text-transform:uppercase; color:#475569; }
    .kpi-value { font-size:45px; font-weight:900; line-height:1.15; margin-top:4px; color:#0D2350; }
    .kpi-sub   { font-size:18px; font-weight:800; color:#2563EB; margin-top:2px; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        border: none !important; color: #0f172a !important;
        font-weight: 900 !important; font-size: 20px !important; padding: 11px !important;
    }
    /* Tiêu đề điều hướng trong sidebar */
    .nav-title {
        color: #050E3C; font-size: 20px; font-weight: 900; text-transform: uppercase;
        letter-spacing: 0.5px; margin: 4px 0 8px 0; text-align: center;
    }
    /* Nút điều hướng trang: to, bo góc, dễ bấm */
    section[data-testid="stSidebar"] .stButton > button {
        font-size: 21px !important; font-weight: 900 !important;
        padding: 15px 10px !important; border-radius: 12px !important;
        border: 2px solid #050E3C !important; margin-bottom: 6px !important;
        transition: all 0.15s ease;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(5,14,60,0.25) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
STAFF_CONFIG = {
   "Andres Nguyen": "GOLD",
    "Charlie Nguyen": "GOLD",
    "Alan Nguyen": "GOLD",
    "Rio Le": "GOLD",
    "Ryan Le": "GOLD",
    "Amy Tran": "SILVER",
    "William Nguyen": "SILVER",
    "Thierry Phung": "BRONZE",
    "David Vo": "BRONZE",
    "Kathy Bui": "BRONZE",
    "Ivan Huynh": "Associated",
    "Jayce Mai": "Associated",
    "Jolie Nguyen": "Associated",
    "Louisa Ngo": "Associated",
    "Tony Pham": "Associated",
    "Katny Duong": "Associated",
    "Liam Hoang": "Probation",
    "Claire Dinh": "Probation",
    "Mia Bui": "Associated",
    "Niko Nguyen": "Probation",
    "Martin Tran": "Probation",
    "Ray Duong": "Probation",
    "Marky Huynh": "Probation"
}
STAFF_LIST = list(STAFF_CONFIG.keys())
LEVEL_TARGETS = {"GOLD": 9000, "SILVER": 9000, "BRONZE": 9000, "Associated": 9000, "Probation": 9000}
LEVEL_COLORS = {"GOLD": "#FDE9B8", "SILVER": "#E4EAF1", "BRONZE": "#F1DAC4", "Associated": "#DAE6FB", "Probation": "#D2F0E1"}
LEVEL_TEXT   = {"GOLD": "#8A6D0B", "SILVER": "#475569", "BRONZE": "#9A5A24", "Associated": "#1E40AF", "Probation": "#0F766E"}


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

def extract_report_range(df):
    if 'Date' not in df.columns:
        return (None, None, 0)
    s = pd.to_datetime(df['Date'].astype(str).str.strip(), format='%a %m/%d/%Y', errors='coerce').dropna()
    if len(s) == 0:
        return (None, None, 0)
    days = sorted(pd.Series(s.dt.normalize().unique()))
    dfrom = pd.Timestamp(days[0]).strftime('%m/%d/%Y')
    dto = pd.Timestamp(days[-1]).strftime('%m/%d/%Y')
    return (dfrom, dto, len(days))

def count_working_days(date_from, date_to):
    """Team làm 5 ngày/tuần (Chủ Nhật→Thứ Năm), OFF Thứ Sáu & Thứ Bảy.
    Trả về số ngày làm việc thực tế trong khoảng ngày (dùng để nhân goal thay vì nhân theo số ngày lịch)."""
    d0 = pd.to_datetime(date_from, errors='coerce')
    d1 = pd.to_datetime(date_to, errors='coerce')
    if pd.isna(d0) or pd.isna(d1):
        return 0
    rng = pd.date_range(d0.normalize(), d1.normalize(), freq='D')
    OFF_WEEKDAYS = [4, 5]  # pandas: Thứ Hai=0 ... Thứ Sáu=4, Thứ Bảy=5, Chủ Nhật=6
    return int((~rng.dayofweek.isin(OFF_WEEKDAYS)).sum())

def detect_period_label(date_from, date_to):
    """Nhận diện khoảng dữ liệu là Ngày / Tuần / Tháng / Năm để hiển thị & tổng hợp cho đúng."""
    d0 = pd.to_datetime(date_from, errors='coerce')
    d1 = pd.to_datetime(date_to, errors='coerce')
    if pd.isna(d0) or pd.isna(d1):
        return "NGÀY"
    span = (d1.normalize() - d0.normalize()).days + 1
    if span <= 1: return "NGÀY"
    if span <= 7: return "TUẦN"
    if span <= 31: return "THÁNG"
    return "NĂM"

def dedup_extension_placeholder_rows(df_raw):
    """RingCentral đôi khi ghi 2 dòng cho CÙNG 1 cuộc gọi Outgoing:
    - dòng 'nháp' lúc cuộc gọi mới định tuyến qua tổng đài: cột From = SỐ EXTENSION nội bộ (vd '290')
    - dòng 'hoàn chỉnh' khi cuộc gọi đã ra line ngoài: cột From = SỐ ĐIỆN THOẠI thật (vd '(678) 680-5004')
    Bình thường dòng nháp mãi ở trạng thái 'In Progress' (0 giây, vô hại). Nhưng nếu export đúng lúc cuộc
    gọi vừa kết thúc, cả 2 dòng đều có thời lượng đầy đủ -> bị đếm dư 1 cuộc + dư talktime khi chạy file
    tổng nhiều extension (dòng nháp không xuất hiện trong file chỉ lọc riêng 1 extension).
    Xoá dòng nháp khi đã có dòng hoàn chỉnh trùng Extension/Ngày/Giờ/Số gọi đến/Thời lượng."""
    if 'From' not in df_raw.columns or 'Extension' not in df_raw.columns or 'Direction' not in df_raw.columns:
        return df_raw, 0
    d = df_raw.reset_index(drop=True)
    ext_num = d['Extension'].astype(str).str.extract(r'^\s*(\d+)')[0]
    is_outgoing = d['Direction'].astype(str).str.strip().str.lower() == 'outgoing'
    is_placeholder = is_outgoing & (d['From'].astype(str).str.strip() == ext_num)
    if not is_placeholder.any():
        return d, 0
    key_cols = ['Extension', 'Date', 'Time', 'To', 'Duration']
    real_keys = d.loc[is_outgoing & ~is_placeholder, key_cols].drop_duplicates().copy()
    real_keys['_has_real'] = True
    merged = d.merge(real_keys, on=key_cols, how='left')
    drop_mask = (is_placeholder & merged['_has_real'].fillna(False)).to_numpy()
    n_removed = int(drop_mask.sum())
    if n_removed == 0:
        return d, 0
    return d.loc[~drop_mask].reset_index(drop=True), n_removed

def _parse_ext_name(ext):
    if pd.isna(ext): return "Unknown"
    s = str(ext).strip()
    if ' - ' not in s: return s
    a, b = [p.strip() for p in s.split(' - ', 1)]
    if a in STAFF_LIST: return a
    if b in STAFF_LIST: return b
    if re.match(r'^\d+$', a): return b
    if re.match(r'^\d+$', b): return a
    return b

# --- 3. GOOGLE SHEET: NGUỒN DỮ LIỆU CHỐT / GIẢM SỐ P / OFF ---
# Sheet "Bảng Theo Dõi Sales Tháng 7 - Tháng 12/2026": mỗi tháng 1 tab (thang_7 ... thang_12).
# Cấu trúc mỗi tab: dòng 1 = ngày (mm/dd/yyyy), lặp lại mỗi 3 cột; dòng 2 = nhãn con
# ("" = Chốt, "Giảm số P", "OFF"); dòng 3 trở đi = dữ liệu theo TÊN (first name).
DEFAULT_GSHEET_URL = "https://docs.google.com/spreadsheets/d/1OcOojRmbSGHthGBqfckHMZZSaImT7fKSGdoiETsdfAw/edit?gid=1882738468#gid=1882738468"
try:
    DEFAULT_GSHEET_URL = st.secrets.get("GSHEET_URL", DEFAULT_GSHEET_URL)
except Exception:
    pass

MONTH_SHEET_NAMES = {7: "thang_7", 8: "thang_8", 9: "thang_9", 10: "thang_10", 11: "thang_11", 12: "thang_12"}

# Tên trên Google Sheet chỉ ghi first name (Andres, Charlie...) -> map ngược về tên đầy đủ trong STAFF_LIST
FIRST_NAME_TO_FULL = {}
for _full in STAFF_LIST:
    _fn = _full.split()[0]
    if _fn in FIRST_NAME_TO_FULL:
        st.sidebar.warning(f"⚠️ Trùng first name '{_fn}' giữa '{FIRST_NAME_TO_FULL[_fn]}' và '{_full}' — kiểm tra STAFF_CONFIG.")
    FIRST_NAME_TO_FULL[_fn] = _full

def _extract_sheet_id(url_or_id):
    m = re.search(r'/d/([a-zA-Z0-9-_]+)', str(url_or_id))
    return m.group(1) if m else str(url_or_id).strip()

def _month_csv_url(sheet_id, sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

def _parse_money_vn(v):
    """Chốt $ trên sheet ghi kiểu VN: '$150,00' (dấu phẩy = thập phân)."""
    if pd.isna(v): return 0.0
    s = str(v).strip()
    if s in ('', '-'): return 0.0
    s = s.replace('$', '').replace(' ', '')
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except Exception:
        return 0.0

def _parse_off_flag(v):
    if pd.isna(v): return False
    return str(v).strip().lower() not in ('', '0', 'false', 'no', 'không', 'khong')

@st.cache_data(ttl=15, show_spinner=False)
def _fetch_month_raw(sheet_id, sheet_name):
    url = _month_csv_url(sheet_id, sheet_name)
    return pd.read_csv(url, header=None, dtype=str)

def _parse_month_sheet(raw):
    """Chuyển 1 tab (dạng lịch ngang) thành bảng dài: Date | Sales Name | Chốt | Giảm số P | OFF."""
    cols = ['Date', 'Sales Name', 'Chốt', 'Giảm số P', 'OFF']
    if raw is None or len(raw) < 3 or raw.shape[1] < 4:
        return pd.DataFrame(columns=cols)
    header_dates = raw.iloc[0]
    data = raw.iloc[2:]
    records = []
    ncols = raw.shape[1]
    col = 1
    while col + 2 < ncols:
        dt = pd.to_datetime(str(header_dates[col]).strip(), format='%m/%d/%Y', errors='coerce')
        if pd.isna(dt):
            col += 3
            continue
        for _, row in data.iterrows():
            full = FIRST_NAME_TO_FULL.get(str(row[0]).strip())
            if not full:
                continue
            records.append((
                dt, full,
                _parse_money_vn(row[col]),
                _parse_money_vn(row[col + 1]),
                _parse_off_flag(row[col + 2]),
            ))
        col += 3
    return pd.DataFrame(records, columns=cols)

def load_sheet_range(sheet_id, date_from, date_to):
    d0 = pd.to_datetime(date_from, errors='coerce')
    d1 = pd.to_datetime(date_to, errors='coerce')
    cols = ['Date', 'Sales Name', 'Chốt', 'Giảm số P', 'OFF']
    if pd.isna(d0) or pd.isna(d1):
        return pd.DataFrame(columns=cols)
    frames, months_used, months_missing = [], [], []
    # Dùng period_range theo THÁNG để chạy đúng khi dữ liệu là 1 tuần/1 tháng/1 năm,
    # kể cả khi khoảng ngày vắt qua nhiều năm (vd 12/2026 -> 01/2027).
    for p in pd.period_range(d0.to_period('M'), d1.to_period('M'), freq='M'):
        sheet_name = MONTH_SHEET_NAMES.get(p.month)
        if not sheet_name:
            months_missing.append(f"thang_{p.month}")
            continue
        try:
            raw = _fetch_month_raw(sheet_id, sheet_name)
        except Exception as e:
            st.sidebar.error(f"Không đọc được tab '{sheet_name}': {e}")
            continue
        frames.append(_parse_month_sheet(raw))
        months_used.append(sheet_name)
    st.session_state['_gsheet_months_used'] = months_used
    st.session_state['_gsheet_months_missing'] = months_missing
    if not frames:
        return pd.DataFrame(columns=cols)
    allrows = pd.concat(frames, ignore_index=True)
    return allrows[(allrows['Date'] >= d0.normalize()) & (allrows['Date'] <= d1.normalize())]

def gsheet_apply(url_or_id, date_from, date_to):
    """Nạp Chốt $ / Xin OFF / Giảm số P từ đúng tab tháng vào input_df. Trả về số dòng đã khớp."""
    sheet_id = _extract_sheet_id(url_or_id)
    sel = load_sheet_range(sheet_id, date_from, date_to)
    idf = st.session_state.input_df
    single = (date_from == date_to)
    n = 0
    if single:
        for nm, g in sel.groupby('Sales Name'):
            if nm not in idf.index: continue
            r = g.iloc[-1]
            idf.loc[nm, 'Chốt $'] = float(r['Chốt'])
            idf.loc[nm, 'Xin OFF'] = bool(r['OFF'])
            idf.loc[nm, 'Giảm số P'] = float(r['Giảm số P'])
            n += 1
    else:
        agg = sel.groupby('Sales Name')[['Chốt', 'Giảm số P']].sum()
        for nm, row in agg.iterrows():
            if nm not in idf.index: continue
            idf.loc[nm, 'Chốt $'] = float(row['Chốt'])
            idf.loc[nm, 'Giảm số P'] = float(row['Giảm số P'])
            n += 1
    return n

# --- 4. SESSION STATE ---
if 'input_df' not in st.session_state:
    st.session_state.input_df = pd.DataFrame({
        "Sales Name": STAFF_LIST, "Chốt $": 0.0, "Xin OFF": False, "Giảm số P": 0.0
    }).set_index("Sales Name")

# --- 5. SIDEBAR ---
st.sidebar.markdown("# 💎 Master Dashboard")
st.sidebar.caption(f"🛠️ Code version: **{APP_VERSION}**")
uploaded_file = st.sidebar.file_uploader("📂 Tải file RingCentral", type=["csv"])

with st.sidebar.expander("🔗 Google Sheet Chốt / Giảm số P / OFF", expanded=False):
    gs_url = st.text_input("Link Google Sheet (hoặc Sheet ID)",
                           value=st.session_state.get("gsheet_url", DEFAULT_GSHEET_URL),
                           help="Mặc định đã gắn sẵn link 'Bảng Theo Dõi Sales Tháng 7 - Tháng 12/2026'.")
    st.session_state["gsheet_url"] = gs_url
    if st.button("🔄 Đồng bộ lại từ Google Sheet", use_container_width=True):
        _fetch_month_raw.clear()
        st.rerun()
    st.caption("Web tự chọn đúng tab **thang_7 → thang_12** theo tháng của dữ liệu RingCentral đang tải lên "
               "(khoảng ngày lệch qua nhiều tháng sẽ tự gộp nhiều tab). Tự làm mới ~15 giây/lần.")

HISTORY_DIR = "history"
os.makedirs(HISTORY_DIR, exist_ok=True)

if 'page' not in st.session_state:
    st.session_state.page = "📊 Báo cáo & Biểu đồ"
st.sidebar.markdown("---")
st.sidebar.markdown('<div class="nav-title">📄 Chọn trang</div>', unsafe_allow_html=True)
_nav = [("📊 Báo cáo & Biểu đồ", "📊  BÁO CÁO & BIỂU ĐỒ"),
        ("📅 Lịch sử", "📅  LỊCH SỬ (NGÀY CŨ)")]
for _val, _label in _nav:
    if st.sidebar.button(_label, use_container_width=True,
                         type=("primary" if st.session_state.page == _val else "secondary")):
        st.session_state.page = _val; st.rerun()
page = st.session_state.page

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
    df_raw.columns = df_raw.columns.str.strip()
    df_raw, n_dedup = dedup_extension_placeholder_rows(df_raw)

    date_from, date_to, n_days = extract_report_range(df_raw)
    is_range = bool(date_from and date_to and date_from != date_to)
    report_date = date_from
    period_label = detect_period_label(date_from, date_to) if date_from else "NGÀY"
    working_days = count_working_days(date_from, date_to) if (is_range and date_from) else 1
    if date_from:
        if is_range:
            file_date = f"{date_from.replace('/','-')}_den_{date_to.replace('/','-')}"
            static_time = (f"{date_from} → {date_to}  ({n_days} ngày lịch, "
                           f"{working_days} ngày làm việc) | {now.strftime('%H:%M')}")
        else:
            file_date = date_from.replace('/', '-')
            static_time = f"{date_from} | {now.strftime('%H:%M')}"

    if n_dedup:
        st.sidebar.caption(f"🧹 Đã gộp {n_dedup} dòng bị RingCentral log trùng (cuộc gọi Outgoing bị ghi 2 dòng).")

    n_incoming = 0
    if 'Direction' in df_raw.columns:
        _dir = df_raw['Direction'].astype(str).str.strip().str.lower()
        n_incoming = int((_dir == 'incoming').sum())
        df_raw = df_raw[_dir == 'outgoing']
        if n_incoming:
            st.sidebar.caption(f"🚫 Đã loại {n_incoming} dòng Incoming khỏi talktime.")
    else:
        st.warning("⚠️ Không tìm thấy cột 'Direction'. Vui lòng kiểm tra lại định dạng file.")

    if 'Action' in df_raw.columns:
        df_raw['is_tr'] = df_raw['Action'].astype(str).str.strip().str.lower() == 'transfer'
    elif 'Type' in df_raw.columns:
        df_raw['is_tr'] = df_raw['Type'].astype(str).str.strip().str.lower() != 'voice'
    else:
        df_raw['is_tr'] = False

    df_raw['Ext_Name'] = df_raw['Extension'].apply(_parse_ext_name)
    df_raw['Sec'] = df_raw['Duration'].apply(to_seconds)
    df_raw['Start'] = pd.to_datetime(
        df_raw['Date'].astype(str).str.strip() + ' ' + df_raw['Time'].astype(str).str.strip(),
        format='%a %m/%d/%Y %I:%M %p', errors='coerce')
    df_raw = df_raw.dropna(subset=['Start'])
    df_raw['End'] = df_raw['Start'] + pd.to_timedelta(df_raw['Sec'], unit='s')

    active_in_file = df_raw['Ext_Name'].unique()
    active_staff = list(STAFF_LIST)
    no_data_staff = [n for n in active_staff if n not in active_in_file]
    NO_DATA_SET = set(no_data_staff)

    def _agg_calls(g):
        g = g.sort_values('Start')
        contribs, session = [], None

        def _flush():
            nonlocal session
            if session and session['legs']:
                if session['has_transfer']:
                    contribs.append(max(session['legs']))
                else:
                    contribs.extend(session['legs'])
            session = None

        for s, e, sec, is_tr in zip(g['Start'], g['End'], g['Sec'], g['is_tr']):
            if is_tr:
                if session is None:
                    session = {'legs': [], 'end': e, 'has_transfer': True, 'bridge': True}
                else:
                    session['has_transfer'] = True
                    session['bridge'] = True
                    session['end'] = max(session['end'], e)
                continue
            if session is None:
                session = {'legs': [sec], 'end': e, 'has_transfer': False, 'bridge': False}
            elif s <= session['end'] or session['bridge']:
                session['legs'].append(sec)
                session['end'] = max(session['end'], e)
                session['bridge'] = False
            else:
                _flush()
                session = {'legs': [sec], 'end': e, 'has_transfer': False, 'bridge': False}
        _flush()

        ss = pd.Series(contribs, dtype=float)
        return pd.Series({
            'Actual_Sec': float(ss.sum()),
            'Tong_Cuoc_Goi': int(len(ss)),
            'Int_5p':  int(((ss >= 300) & (ss < 600)).sum()),
            'Int_10p': int(((ss >= 600) & (ss < 1800)).sum()),
            'Int_30p': int((ss >= 1800).sum()),
        })

    df_active = df_raw[df_raw['Ext_Name'].isin(active_staff)]
    if len(df_active):
        stats = df_active.groupby('Ext_Name').apply(_agg_calls).reindex(active_staff).fillna(0)
    else:
        stats = pd.DataFrame(
            0, index=active_staff,
            columns=['Actual_Sec', 'Tong_Cuoc_Goi', 'Int_5p', 'Int_10p', 'Int_30p']
        )

    st.session_state['active_staff'] = active_staff

    _gs = st.session_state.get("gsheet_url", "").strip()
    if _gs and date_from:
        st.session_state.input_df.loc[active_staff, ['Chốt $', 'Xin OFF', 'Giảm số P']] = [0.0, False, 0.0]
        _n = gsheet_apply(_gs, date_from, date_to)
        _months = st.session_state.get('_gsheet_months_used', [])
        _missing = st.session_state.get('_gsheet_months_missing', [])
        _lbl = (f"{date_from}→{date_to} (cộng dồn Chốt & Giảm số P)" if is_range else f"ngày {date_from}")
        _mtxt = f" [tab: {', '.join(_months)}]" if _months else " [không tìm thấy tab tháng phù hợp]"
        st.sidebar.caption(f"🔗 Google Sheet: đã nạp {_n} dòng — {_lbl}{_mtxt}")
        if _missing:
            st.sidebar.warning(f"⚠️ Sheet chưa có tab cho: {', '.join(sorted(set(_missing)))} — Chốt $ các tháng này = 0.")

    staff_input_df = st.session_state.input_df.loc[active_staff]

    final_df = pd.concat([staff_input_df, stats], axis=1).fillna(0).reset_index()
    final_df.rename(columns={'index': 'Sales Name'}, inplace=True)

    # Goal nhân theo số NGÀY LÀM VIỆC thực tế (5 ngày/tuần, OFF Thứ 6 & Thứ 7) — không nhân theo số ngày lịch.
    _days_mult = working_days if (is_range and working_days > 0) else 1
    def calculate_metrics(row):
        name = row['Sales Name']; lvl = STAFF_CONFIG.get(name, "Probation")
        target_orig = LEVEL_TARGETS.get(lvl, 9000) * _days_mult
        actual = row['Actual_Sec']
        giam_p = float(row['Giảm số P'])
        if row['Xin OFF']:
            return pd.Series([lvl, target_orig, giam_p, actual, actual, 0.0, "OFF"])
        sales = row['Chốt $']
        if name in NO_DATA_SET and sales == 0:
            return pd.Series([lvl, target_orig, giam_p, 0, 0, 0.0, "NO DATA"])
        if is_range:
            goal = target_orig
            total = actual + giam_p * 60
            pct = 100.0 if goal <= 0 else total / goal * 100
            return pd.Series([lvl, goal, giam_p, actual, total, round(float(pct), 1),
                              "GOOD JOB" if pct >= 100 else "COME ON!"])
        is_done = sales >= 2000
        bonus = 1800 if 300 <= sales < 500 else (2700 if 500 <= sales < 1000 else (5400 if 1000 <= sales < 2000 else 0))
        goal = 0 if is_done else max(0, target_orig - bonus)
        total = actual + giam_p * 60
        pct = 100.0 if (is_done or goal <= 0) else total / goal * 100
        return pd.Series([lvl, goal, giam_p, actual, total, round(float(pct), 1),
                          "GOOD JOB" if (pct >= 100 or is_done) else "COME ON!"])

    final_df[['🏅 LVL', 'goal_val', 'giam_p', 'actual_val', 'total_val', 'pct_val', '📊 RESULT']] = final_df.apply(calculate_metrics, axis=1)
    _vv = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])]
    max_pct = float(_vv['pct_val'].max()) if len(_vv) and _vv['pct_val'].max() > 0 else 100.0
    final_df = final_df.reset_index(drop=True)

# ==================== TRANG 2: BÁO CÁO ====================
if uploaded_file and page == "📊 Báo cáo & Biểu đồ":
    t_p = int(final_df['Chốt $'].sum())
    t_t = format_time(final_df['Actual_Sec'].sum())
    t_c = int(final_df['Tong_Cuoc_Goi'].sum())
    _valid = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])]
    team_pct = round(_valid['total_val'].sum() / _valid['goal_val'].sum() * 100, 1) if _valid['goal_val'].sum() > 0 else 0.0
    n_done = int((final_df['📊 RESULT'] == "GOOD JOB").sum())
    n_active = int(len(_valid))

    valid = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])]
    tot_goal = valid['goal_val'].sum()
    tot_total = valid['total_val'].sum()
    tot_pct = round(tot_total / tot_goal * 100, 1) if tot_goal > 0 else 0.0

    def _nd(r, v):
        return "—" if r['📊 RESULT'] == "NO DATA" else v
    disp_df = pd.DataFrame()
    disp_df['👤 SALES'] = final_df['Sales Name']
    disp_df['🏅 LVL'] = final_df['🏅 LVL']
    disp_df['💵 CHỐT $'] = final_df['Chốt $']
    disp_df['🎯 GOAL'] = final_df.apply(lambda r: _nd(r, format_time(r['goal_val'])), axis=1)
    disp_df['➖ GIẢM SỐ P'] = final_df.apply(lambda r: _nd(r, f"{int(r['giam_p'])}p"), axis=1)
    disp_df['⏱️ CALL'] = final_df.apply(lambda r: _nd(r, format_time(r['actual_val'])), axis=1)
    disp_df['🧮 TOTAL'] = final_df.apply(lambda r: _nd(r, format_time(r['total_val'])), axis=1)
    disp_df['% HOÀN THÀNH'] = final_df['pct_val']
    disp_df['📞 TỔNG CUỘC'] = final_df['Tong_Cuoc_Goi'].astype(int)
    disp_df['🔥 5P'] = final_df['Int_5p'].astype(int)
    disp_df['🔥 10P'] = final_df['Int_10p'].astype(int)
    disp_df['🔥 30P'] = final_df['Int_30p'].astype(int)
    disp_df['Σ >5P'] = (final_df['Int_5p'] + final_df['Int_10p'] + final_df['Int_30p']).astype(int)
    disp_df['📊 RESULT'] = final_df['📊 RESULT']

    total_row = {
        '👤 SALES': '🔷 TOTAL', '🏅 LVL': '',
        '💵 CHỐT $': float(final_df['Chốt $'].sum()),
        '🎯 GOAL': format_time(tot_goal),
        '➖ GIẢM SỐ P': f"{int(valid['giam_p'].sum())}p",
        '⏱️ CALL': format_time(final_df['actual_val'].sum()),
        '🧮 TOTAL': format_time(tot_total),
        '% HOÀN THÀNH': tot_pct,
        '📞 TỔNG CUỘC': int(final_df['Tong_Cuoc_Goi'].sum()),
        '🔥 5P': int(final_df['Int_5p'].sum()),
        '🔥 10P': int(final_df['Int_10p'].sum()),
        '🔥 30P': int(final_df['Int_30p'].sum()),
        'Σ >5P': int((final_df['Int_5p'] + final_df['Int_10p'] + final_df['Int_30p']).sum()),
        '📊 RESULT': '',
    }
    disp_df = pd.concat([disp_df, pd.DataFrame([total_row])], ignore_index=True)

    if no_data_staff:
        st.warning(f"📝 **Không có dữ liệu talktime ({len(no_data_staff)}):** " + " • ".join(no_data_staff))

    def _bar_green(pct, label):
        p = max(0, min(pct, 100))
        return (f'<div class="pbar"><div class="pfill" style="width:{p:.0f}%;background:#A7D8B0;"></div>'
                f'<span style="color:#1E5631;">{label}</span></div>')

    def _bar_pct(rel_w, real_pct, label):
        p = max(0, min(rel_w, 100))
        if real_pct >= 100: fill, txt = "#EF4444", "#ffffff"
        else:               fill, txt = "#FDE68A", "#7A5B00"
        return (f'<div class="pbar"><div class="pfill" style="width:{p:.0f}%;background:{fill};"></div>'
                f'<span style="color:{txt};">{label}</span></div>')

    def _heat_style(value, vmax, rgb):
        """Thang màu: đậm/nhạt theo giá trị lớn/nhỏ trong cột (so với giá trị max của cột)."""
        if vmax <= 0 or value <= 0:
            return ''
        alpha = 0.22 + min(1.0, value / vmax) * 0.72
        r, g, b = rgb
        txt = '#ffffff' if alpha >= 0.50 else '#1f2937'
        return f'style="background:rgba({r},{g},{b},{alpha:.2f});color:{txt};font-weight:900;"'

    _hv = final_df[final_df['📊 RESULT'] != "NO DATA"]
    _max_giam = float(_hv['giam_p'].max()) if len(_hv) else 0.0
    _max_5p = float(_hv['Int_5p'].max()) if len(_hv) else 0.0
    _max_10p = float(_hv['Int_10p'].max()) if len(_hv) else 0.0
    _max_30p = float(_hv['Int_30p'].max()) if len(_hv) else 0.0
    _sum5_series = _hv['Int_5p'] + _hv['Int_10p'] + _hv['Int_30p']
    _max_sum5 = float(_sum5_series.max()) if len(_sum5_series) else 0.0
    COL_GIAM = (245, 158, 11)   # amber
    COL_5P   = (20, 184, 166)   # teal
    COL_10P  = (59, 130, 246)   # blue
    COL_30P  = (239, 68, 68)    # red
    COL_SUM5 = (99, 102, 241)   # indigo

    # Top 5 nhân viên có TỔNG CUỘC PHONE nhiều nhất — tô nổi bật theo hạng
    _top5 = _hv.nlargest(5, 'Tong_Cuoc_Goi') if len(_hv) else _hv
    _top5_rank = {name: i + 1 for i, name in enumerate(_top5['Sales Name'])}
    TOP5_STYLE = {
        1: 'background:linear-gradient(135deg,#FFD700,#F5B301);color:#5C3D00;font-weight:900;',
        2: 'background:linear-gradient(135deg,#E2E8F0,#B8C2CC);color:#1E293B;font-weight:900;',
        3: 'background:linear-gradient(135deg,#E8B27D,#C9793C);color:#4A2A0A;font-weight:900;',
        4: 'background:#BFDBFE;color:#1E3A8A;font-weight:900;',
        5: 'background:#BFDBFE;color:#1E3A8A;font-weight:900;',
    }
    TOP5_ICON = {1: '🥇', 2: '🥈', 3: '🥉', 4: '🏅', 5: '🏅'}

    rows_html = ""
    for _, r in final_df.iterrows():
        res = r['📊 RESULT']; lvl = r['🏅 LVL']
        s5, s10, s30 = int(r["Int_5p"]), int(r["Int_10p"]), int(r["Int_30p"])
        if res == "NO DATA":
            rows_html += (f'<tr class="nod"><td style="font-weight:900;">{r["Sales Name"]}</td><td>{lvl}</td>'
                          f'<td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td>'
                          f'<td>0</td><td>{s5}</td><td>{s10}</td><td>{s30}</td><td>{s5+s10+s30}</td>'
                          f'<td class="badge nodb">NO DATA</td></tr>')
            continue
        lvl_bg = LEVEL_COLORS.get(lvl, "#FFFFFF"); lvl_tx = LEVEL_TEXT.get(lvl, "#12326B")
        chot = f"${int(r['Chốt $']):,}" if r['Chốt $'] > 0 else "$0"
        _c = r['Chốt $']
        if _c >= 300:   chot_style = 'style="background:#F87171;color:#7F1D1D;font-weight:900;"'
        elif _c >= 100: chot_style = 'style="background:#FDBA74;color:#7C2D12;font-weight:900;"'
        elif _c >= 1:   chot_style = 'style="background:#FDE68A;color:#854D0E;font-weight:900;"'
        else:           chot_style = ''
        total_bar = _bar_green(r['total_val'] / r['goal_val'] * 100 if r['goal_val'] > 0 else 100,
                               format_time(r['total_val']))
        pct_bar = _bar_pct(r['pct_val'] / max_pct * 100, r['pct_val'], f"{r['pct_val']:.0f}%")
        if res == "GOOD JOB": badge = '<td class="badge okb">GOOD JOB</td>'
        elif res == "OFF":    badge = '<td class="badge offb">OFF</td>'
        else:                 badge = '<td class="badge cmb">COME ON!</td>'
        giam_style = _heat_style(r['giam_p'], _max_giam, COL_GIAM)
        s5_style = _heat_style(s5, _max_5p, COL_5P)
        s10_style = _heat_style(s10, _max_10p, COL_10P)
        s30_style = _heat_style(s30, _max_30p, COL_30P)
        sum5_style = _heat_style(s5 + s10 + s30, _max_sum5, COL_SUM5)
        _rank = _top5_rank.get(r['Sales Name'])
        if _rank:
            tc_style = f'style="{TOP5_STYLE[_rank]}"'
            tc_val = f'{TOP5_ICON[_rank]} {int(r["Tong_Cuoc_Goi"])}'
        else:
            tc_style = ''
            tc_val = f'{int(r["Tong_Cuoc_Goi"])}'
        rows_html += (f'<tr><td style="font-weight:900;">{r["Sales Name"]}</td>'
                      f'<td style="background:{lvl_bg};color:{lvl_tx};font-weight:900;">{lvl}</td>'
                      f'<td {chot_style}>{chot}</td>'
                      f'<td>{format_time(r["goal_val"])}</td>'
                      f'<td {giam_style}>{int(r["giam_p"])}p</td>'
                      f'<td>{format_time(r["actual_val"])}</td>'
                      f'<td>{total_bar}</td><td>{pct_bar}</td>'
                      f'<td {tc_style}>{tc_val}</td>'
                      f'<td {s5_style}>{s5}</td><td {s10_style}>{s10}</td><td {s30_style}>{s30}</td>'
                      f'<td {sum5_style}><b style="font-weight:900;">{s5+s10+s30}</b></td>'
                      f'{badge}</tr>')
    T5, T10, T30 = int(final_df["Int_5p"].sum()), int(final_df["Int_10p"].sum()), int(final_df["Int_30p"].sum())
    rows_html += (f'<tr class="tot"><td style="font-weight:900;">TOTAL</td><td></td>'
                  f'<td>${int(final_df["Chốt $"].sum()):,}</td>'
                  f'<td>{format_time(tot_goal)}</td>'
                  f'<td>{int(valid["giam_p"].sum())}p</td>'
                  f'<td>{format_time(final_df["actual_val"].sum())}</td>'
                  f'<td>{format_time(tot_total)}</td>'
                  f'<td>{tot_pct:.0f}%</td>'
                  f'<td>{int(final_df["Tong_Cuoc_Goi"].sum())}</td>'
                  f'<td>{T5}</td><td>{T10}</td><td>{T30}</td><td>{T5+T10+T30}</td><td></td></tr>')

    kpi_html = f"""
      <div class="kpis">
        <div class="kpi"><div class="ic" style="background:#FEF0D6;">💰</div><div class="lb">Total Premium</div><div class="vl">${t_p:,}</div></div>
        <div class="kpi"><div class="ic" style="background:#D9F0FB;">⏱️</div><div class="lb">Total Talktime</div><div class="vl">{t_t}</div></div>
        <div class="kpi"><div class="ic" style="background:#E4E7FB;">📞</div><div class="lb">Outgoing Calls</div><div class="vl">{t_c:,}</div></div>
        <div class="kpi"><div class="ic" style="background:#D6F5E5;">✅</div><div class="lb">Team hoàn thành</div><div class="vl">{team_pct:.0f}%</div></div>
        <div class="kpi"><div class="ic" style="background:#FCEFCF;">🏆</div><div class="lb">Đạt mục tiêu</div><div class="vl">{n_done}<span style="font-size:25px;color:#7C8798;">/{n_active}</span></div></div>
      </div>"""

    n_rows = len(final_df) + 1
    box_h = 280 + n_rows * 64 + 90
    full_html = f"""
    <div id="reportBox" class="wrap">
      <button class="fsbtn" onclick="goFS()">⛶ Toàn màn hình</button>
      <div class="title">🏆 WORKING RESULTS STATISTICS ({period_label}) | {static_time} (EST)</div>
      {kpi_html}
      <table>
        <thead><tr>
          <th>SALES</th><th>LVL</th><th>CHỐT $</th><th>GOAL</th><th>GIẢM SỐ P</th><th>CALL</th>
          <th>TOTAL</th><th>% HOÀN THÀNH</th><th>TỔNG CUỘC</th>
          <th>5P</th><th>10P</th><th>30P</th><th>Σ&gt;5P</th><th>RESULT</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
      * {{ box-sizing:border-box; font-family:'Inter','Segoe UI',Roboto,Arial,sans-serif; font-weight:700; }}
      body {{ margin:0; }}
      .wrap {{ padding:16px; background:#F6F9FF; position:relative; }}
      #reportBox:fullscreen {{ overflow:auto; }}
      .fsbtn {{ position:absolute; right:18px; top:18px; z-index:9; background:#fff; color:#1F3A66;
                border:1px solid #CBD8EC; border-radius:10px; padding:10px 17px; font-weight:800;
                font-size:17.5px; cursor:pointer; box-shadow:0 2px 6px rgba(30,58,138,.12); }}
      .fsbtn:hover {{ background:#EEF4FF; }}
      .title {{ background:linear-gradient(135deg,#0B1F45,#1D3577); color:#fff; text-align:center;
                font-weight:900; font-size:32.5px; padding:18px; border-radius:14px; letter-spacing:.3px; }}
      .kpis {{ display:flex; gap:14px; margin:16px 0; flex-wrap:wrap; }}
      .kpi {{ flex:1; min-width:168px; text-align:center; background:#fff; border:1px solid #E6ECF5;
              border-radius:16px; padding:16px; box-shadow:0 6px 16px rgba(30,58,138,.07); }}
      .kpi .ic {{ width:48px;height:48px;border-radius:14px;margin:0 auto 8px;display:flex;
                  align-items:center;justify-content:center;font-size:29px; }}
      .kpi .lb {{ font-size:17.5px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;color:#5B6B84; }}
      .kpi .vl {{ font-size:43.75px;font-weight:900;color:#12275A; }}
      table {{ width:100%; border-collapse:separate; border-spacing:0 6px; }}
      th {{ font-size:20.5px; font-weight:900; color:#1E293B; text-align:center; padding:9px 6px;
            text-transform:uppercase; letter-spacing:.2px; }}
      td {{ font-size:20.5px; font-weight:800; text-align:center; padding:11px 6px; background:#fff; color:#0f172a; }}
      tr td:first-child {{ border-radius:12px 0 0 12px; }}
      tr td:last-child  {{ border-radius:0 12px 12px 0; }}
      tr.nod td {{ background:#F3F6FB; color:#7C8798; font-weight:800; }}
      tr.tot td {{ background:#1E3A8A; color:#fff; font-weight:900; font-size:21.9px; }}
      .pbar {{ position:relative; height:27px; background:#EEF2F8; border-radius:8px; overflow:hidden; }}
      .pfill {{ position:absolute; left:0; top:0; bottom:0; }}
      .pbar span {{ position:relative; z-index:2; line-height:27px; font-weight:900; font-size:18px; }}
      .badge {{ border-radius:10px; font-weight:900; }}
      .okb {{ background:#DCFCE7; color:#14532D; }}
      .cmb {{ background:#FEE2E2; color:#7F1D1D; }}
      .offb {{ background:#E2E8F0; color:#1E293B; }}
      .nodb {{ background:#EEF2F8; color:#475569; }}
    </style>
    <script>
      function goFS() {{
        var el = document.getElementById('reportBox');
        var rq = el.requestFullscreen || el.webkitRequestFullscreen || el.msRequestFullscreen;
        if (rq) {{ rq.call(el).catch(function(){{ alert('Trình duyệt chặn toàn màn hình trong khung này. Hãy nhấn F11 để phóng to cả trang.'); }}); }}
        else {{ alert('Trình duyệt không hỗ trợ. Hãy nhấn F11.'); }}
      }}
    </script>
    """

    st.markdown("#### 📋 Bảng phân tích Talktime")
    components.html(full_html, height=box_h, scrolling=True)
    st.caption("🥇🥈🥉🏅 Cột TỔNG CUỘC: tô màu Top 5 nhân viên có số lượng cuộc gọi nhiều nhất.")

    if not is_range:
        with st.expander("📋 Copy cột '% HOÀN THÀNH' để dán sang Google Sheet"):
            st.caption("Bấm biểu tượng copy ở góc phải ô bên dưới → sang Google Sheet, chọn 1 ô rồi Ctrl+V. "
                       "Các dòng sẽ tự đổ xuống thành 1 cột, đúng thứ tự như bảng (kèm dòng TOTAL cuối).")
            pct_with_sign = "\n".join(f"{v:.0f}%" for v in final_df['pct_val']) + f"\n{tot_pct:.0f}%"
            pct_plain = "\n".join(f"{v:.0f}" for v in final_df['pct_val']) + f"\n{tot_pct:.0f}"
            cA, cB = st.columns(2)
            with cA:
                st.markdown("**Có dấu %** (vd 53%)")
                st.code(pct_with_sign, language=None)
            with cB:
                st.markdown("**Số thường** (vd 53, dễ tính toán)")
                st.code(pct_plain, language=None)

    st.markdown("---")
    st.markdown(f'<div class="main-header">📈 DASHBOARD TALKTIME ({period_label})</div>', unsafe_allow_html=True)

    # Dữ liệu Ring Central có thể là 1 ngày / 1 tuần / 1 tháng / 1 năm — tự tổng hợp theo đúng cấp
    # thời gian tương ứng: NGÀY → không cần xu hướng; TUẦN → theo ngày; THÁNG → theo tuần; NĂM → theo tháng.
    if period_label in ("TUẦN", "THÁNG", "NĂM") and len(df_active):
        dfp = df_active.copy()
        if period_label == "TUẦN":
            dfp['_order'] = dfp['Start'].dt.normalize()
            dfp['Bucket'] = dfp['Start'].dt.strftime('%a %d/%m')
            bucket_title, x_title = "theo Ngày", "Ngày"
        elif period_label == "THÁNG":
            iso = dfp['Start'].dt.isocalendar()
            dfp['_order'] = iso['week'].astype(int)
            dfp['Bucket'] = "Tuần " + iso['week'].astype(str)
            bucket_title, x_title = "theo Tuần", "Tuần"
        else:  # NĂM
            dfp['_order'] = dfp['Start'].dt.strftime('%Y%m').astype(int)
            dfp['Bucket'] = dfp['Start'].dt.strftime('%m/%Y')
            bucket_title, x_title = "theo Tháng", "Tháng"

        trend = dfp.groupby(['_order', 'Bucket']).agg(
            Phut=('Sec', lambda x: round(x.sum() / 60, 1)),
            SoCuoc=('Sec', 'count'),
        ).reset_index().sort_values('_order')

        st.markdown(f"**📆 Xu hướng Talktime {bucket_title} (toàn team)**")
        figw = px.bar(trend, x='Bucket', y='Phut', text='Phut', height=340,
                      color='Phut', color_continuous_scale=['#E0E7FF', '#312E81'],
                      hover_data={'SoCuoc': True})
        figw.update_traces(texttemplate='%{text:.0f}p', textposition='outside', cliponaxis=False)
        figw.update_layout(xaxis={'title': x_title, 'categoryorder': 'array', 'categoryarray': trend['Bucket'].tolist()},
                           yaxis_title="Phút", plot_bgcolor='white',
                           margin=dict(t=10, b=0, l=0, r=0), coloraxis_showscale=False)
        st.plotly_chart(figw, use_container_width=True)
        st.caption("Xu hướng tính gộp toàn bộ cuộc gọi outgoing hợp lệ (chưa gộp phiên chuyển máy) — "
                   "chỉ mang tính tham khảo biến động theo thời gian, số liệu chính xác từng Sales xem ở bảng phía trên.")

    tt_df = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])].copy()
    if len(tt_df):
        tt_df['Talktime_Min'] = (tt_df['Actual_Sec'] / 60).round(1)
        tt_df = tt_df.sort_values('Talktime_Min', ascending=False)
        st.markdown("**⏱️ Tổng Talktime theo Sales (phút)**")
        figt = px.bar(tt_df, x='Sales Name', y='Talktime_Min', text='Talktime_Min', height=380,
                      color='Talktime_Min', color_continuous_scale=['#DBEAFE', '#1E3A8A'],
                      hover_data={'Chốt $': ':$,.0f', 'Tong_Cuoc_Goi': True})
        figt.update_traces(texttemplate='%{text:.0f}p', textposition='outside', cliponaxis=False)
        figt.update_layout(xaxis={'title': None, 'tickangle': -40, 'categoryorder': 'total descending'},
                            yaxis_title="Phút", plot_bgcolor='white',
                            margin=dict(t=10, b=0, l=0, r=0), coloraxis_showscale=False)
        st.plotly_chart(figt, use_container_width=True)

    chart_df = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])].copy()
    if len(chart_df):
        def _status(r):
            if r['pct_val'] >= 100 or r['📊 RESULT'] == "GOOD JOB": return "✅ Đạt (≥100%)"
            if r['pct_val'] >= 70: return "🟡 Gần đạt (70–99%)"
            return "🔴 Còn xa (<70%)"
        chart_df['Trạng thái'] = chart_df.apply(_status, axis=1)
        color_map = {"✅ Đạt (≥100%)": "#16a34a", "🟡 Gần đạt (70–99%)": "#f59e0b", "🔴 Còn xa (<70%)": "#dc2626"}
        order = ["✅ Đạt (≥100%)", "🟡 Gần đạt (70–99%)", "🔴 Còn xa (<70%)"]
        chart_df = chart_df.sort_values('pct_val', ascending=False)

        st.markdown("**🎯 % Hoàn thành mục tiêu talktime**")
        fig = px.bar(chart_df, x='Sales Name', y='pct_val', color='Trạng thái',
                     color_discrete_map=color_map, category_orders={'Trạng thái': order},
                     text='pct_val', height=400,
                     hover_data={'Chốt $': ':$,.0f', 'pct_val': ':.1f'})
        fig.update_traces(texttemplate='%{text:.0f}%', textposition='outside', cliponaxis=False)
        fig.add_hline(y=100, line_dash="dash", line_color="#050E3C",
                      annotation_text="Mục tiêu 100%", annotation_position="top left")
        fig.update_layout(
            xaxis={'categoryorder': 'total descending', 'title': None},
            yaxis_title="% Hoàn thành", legend_title=None, plot_bgcolor='white',
            margin=dict(t=40, b=0, l=0, r=0), uniformtext_minsize=8, uniformtext_mode='hide',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

    line_df = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])].copy()
    if len(line_df):
        line_df['Interest'] = line_df['Int_5p'] + line_df['Int_10p'] + line_df['Int_30p']
        tot_5p = int((final_df['Int_5p'] + final_df['Int_10p'] + final_df['Int_30p']).sum())
        st.markdown(f"**📞 Cuộc gọi chất lượng ≥5 phút | Tổng: {tot_5p} cuộc**")
        figl = px.line(line_df, x='Sales Name', y='Interest', markers=True, text='Interest', height=340)
        figl.update_traces(line=dict(color='#050E3C', width=3),
                           marker=dict(size=10, color='#1e3a8a', line=dict(color='white', width=1.5)),
                           textposition='top center', textfont=dict(size=14, color='#050E3C', family='Arial Black'))
        figl.update_layout(
            xaxis={'title': None, 'tickangle': -40},
            yaxis_title="Số cuộc ≥5 phút", plot_bgcolor='white',
            margin=dict(t=20, b=0, l=0, r=0),
            font=dict(size=13, color='#050E3C'))
        figl.update_yaxes(rangemode='tozero', gridcolor='#e2e8f0')
        st.plotly_chart(figl, use_container_width=True)

    lvl_df = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])].copy()
    if len(lvl_df):
        lvl_agg = lvl_df.groupby('🏅 LVL').agg(
            Talktime_Min=('Actual_Sec', lambda x: round(x.sum() / 60, 1)),
            Chốt=('Chốt $', 'sum'),
            Người=('Sales Name', 'count'),
        ).reset_index()
        st.markdown("**🏅 Tổng hợp theo cấp bậc (LVL)**")
        figv = px.bar(lvl_agg, x='🏅 LVL', y='Talktime_Min', text='Talktime_Min', height=320,
                      color='🏅 LVL', color_discrete_map=LEVEL_COLORS,
                      hover_data={'Chốt': ':$,.0f', 'Người': True})
        figv.update_traces(texttemplate='%{text:.0f}p', textposition='outside', cliponaxis=False)
        figv.update_layout(xaxis_title=None, yaxis_title="Tổng phút", plot_bgcolor='white',
                           showlegend=False, margin=dict(t=10, b=0, l=0, r=0))
        st.plotly_chart(figv, use_container_width=True)

    snapshot = final_df[['Sales Name', '🏅 LVL', 'Xin OFF', 'Chốt $',
                         'goal_val', 'giam_p', 'actual_val', 'total_val', 'pct_val',
                         'Tong_Cuoc_Goi', 'Int_5p', 'Int_10p', 'Int_30p', '📊 RESULT']].copy()
    snapshot.insert(0, 'Date', file_date)

    st.markdown("---")
    cc1, cc2, cc3 = st.columns([1.4, 1, 1])
    with cc1:
        if st.button(f"💾 Lưu Final ngày {file_date}", use_container_width=True, type="primary"):
            path = os.path.join(HISTORY_DIR, f"Final_{file_date}.csv")
            snapshot.to_csv(path, index=False, encoding='utf-8-sig')
            st.success(f"✅ Đã lưu: {path}")
    with cc2:
        st.download_button("📥 Tải bảng (CSV)", disp_df.to_csv(index=False).encode('utf-8-sig'),
                           f"Report_{file_date}.csv", use_container_width=True)
    with cc3:
        st.download_button("📦 Tải snapshot", snapshot.to_csv(index=False).encode('utf-8-sig'),
                           f"Snapshot_{file_date}.csv", use_container_width=True)
    saved_path = os.path.join(HISTORY_DIR, f"Final_{file_date}.csv")
    if os.path.exists(saved_path):
        st.caption(f"📁 Ngày {file_date} đã có bản lưu. Bấm 'Lưu' lần nữa sẽ ghi đè.")

# ==================== TRANG 3: LỊCH SỬ ====================
if page == "📅 Lịch sử":
    st.markdown('<div class="main-header">📅 XEM LẠI DỮ LIỆU FINAL CÁC NGÀY</div>', unsafe_allow_html=True)
    files = sorted(glob.glob(os.path.join(HISTORY_DIR, "Final_*.csv")), reverse=True)
    if not files:
        st.info("Chưa có ngày nào được lưu. Vào trang 📊 Báo cáo → bấm '💾 Lưu Final' để lưu lại.")
    else:
        dates = [os.path.basename(f).replace("Final_", "").replace(".csv", "") for f in files]
        sel = st.selectbox("Chọn ngày cần xem lại", dates)
        sdf = pd.read_csv(os.path.join(HISTORY_DIR, f"Final_{sel}.csv"))

        v = sdf[~sdf['📊 RESULT'].isin(["OFF", "NO DATA"])]
        tp = int(sdf['Chốt $'].sum()); tt = format_time(sdf['actual_val'].sum())
        tc = int(sdf['Tong_Cuoc_Goi'].sum())
        _gcol = 'goal_val' if 'goal_val' in sdf.columns else 'target_val'
        _tcol = 'total_val' if 'total_val' in sdf.columns else 'actual_val'
        tpct = round(v[_tcol].sum() / v[_gcol].sum() * 100, 1) if v[_gcol].sum() > 0 else 0.0
        nd = int((sdf['📊 RESULT'] == "GOOD JOB").sum())
        st.markdown(f"""<div class="kpi-row">
            <div class="kpi-card"><div class="kpi-ico" style="background:#F59E0B33;">💰</div>
                <div class="kpi-label">Total Premium</div><div class="kpi-value">${tp:,}</div></div>
            <div class="kpi-card"><div class="kpi-ico" style="background:#38BDF833;">⏱️</div>
                <div class="kpi-label">Total Talktime</div><div class="kpi-value">{tt}</div></div>
            <div class="kpi-card"><div class="kpi-ico" style="background:#818CF833;">📞</div>
                <div class="kpi-label">Outgoing Calls</div><div class="kpi-value">{tc:,}</div></div>
            <div class="kpi-card"><div class="kpi-ico" style="background:#34D39933;">✅</div>
                <div class="kpi-label">Team hoàn thành</div><div class="kpi-value">{tpct:.0f}%</div></div>
            <div class="kpi-card"><div class="kpi-ico" style="background:#FBBF2433;">🏆</div>
                <div class="kpi-label">Đạt mục tiêu</div><div class="kpi-value">{nd}</div></div>
        </div>""", unsafe_allow_html=True)

        show = pd.DataFrame()
        show['👤 SALES'] = sdf['Sales Name']; show['🏅 LVL'] = sdf['🏅 LVL']
        show['💵 CHỐT $'] = sdf['Chốt $']
        show['🎯 GOAL'] = sdf[_gcol].apply(format_time)
        if 'giam_p' in sdf.columns:
            show['➖ GIẢM SỐ P'] = sdf['giam_p'].apply(lambda x: f"{int(x)}p")
        show['⏱️ CALL'] = sdf['actual_val'].apply(format_time)
        show['🧮 TOTAL'] = sdf[_tcol].apply(format_time)
        show['% HOÀN THÀNH'] = sdf['pct_val']
        show['📞 TỔNG CUỘC'] = sdf['Tong_Cuoc_Goi']
        show['🔥 5P'] = sdf['Int_5p']; show['🔥 10P'] = sdf['Int_10p']; show['🔥 30P'] = sdf['Int_30p']
        show['Σ >5P'] = sdf['Int_5p'] + sdf['Int_10p'] + sdf['Int_30p']
        show['📊 RESULT'] = sdf['📊 RESULT']
        st.dataframe(show, use_container_width=True, hide_index=True, height=(len(sdf)*38 + 50),
            column_config={"💵 CHỐT $": st.column_config.NumberColumn(format="$%d"),
                           "% HOÀN THÀNH": st.column_config.NumberColumn(format="%.0f%%")})
        st.download_button("📥 Tải lại file ngày này", sdf.to_csv(index=False).encode('utf-8-sig'),
                           f"Final_{sel}.csv")

# ==================== CHƯA CÓ FILE ====================
if page != "📅 Lịch sử" and not uploaded_file:
    st.info("👋 Chào Team Henry! Tải file RingCentral ở thanh bên để bắt đầu, hoặc vào trang 📅 Lịch sử để xem ngày cũ.")
