import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import os, glob

# --- 1. CẤU HÌNH TRANG & UI LUXURY ---
st.set_page_config(page_title="Dream Talent - Henry Master Hub", layout="wide")

# XỬ LÝ MÚI GIỜ MIỀN ĐÔNG HOA KỲ (EST/EDT)
tz_US_Eastern = pytz.timezone('US/Eastern')
now = datetime.now(tz_US_Eastern)
static_time = now.strftime("%m/%d/%Y | %H:%M")
file_date = now.strftime("%m-%d-%Y")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, .stApp, [data-testid="stAppViewContainer"], [class*="css"] {
        font-family: 'Inter','Segoe UI',Roboto,Arial,sans-serif !important;
    }
    .stApp { background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #050E3C 0%, #1e3a8a 100%);
        color: white; padding: 16px; border-radius: 12px;
        text-align: center; font-weight: 700; font-size: 25px; margin-bottom: 15px;
        letter-spacing: 0.3px;
    }
    /* ===== KPI CARDS (tông NHẠT, căn giữa, chữ to) ===== */
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
        align-items:center; justify-content:center; font-size:23px; margin:0 auto 10px auto;
    }
    .kpi-label { font-size:14px; font-weight:800; letter-spacing:.5px; text-transform:uppercase; color:#64748B; }
    .kpi-value { font-size:36px; font-weight:900; line-height:1.15; margin-top:4px; color:#12326B; }
    .kpi-sub   { font-size:14px; font-weight:700; color:#3B82F6; margin-top:2px; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        border: none !important; color: #0f172a !important;
        font-weight: 900 !important; font-size: 16px !important; padding: 11px !important;
    }
    /* Tiêu đề điều hướng trong sidebar */
    .nav-title {
        color: #050E3C; font-size: 16px; font-weight: 900; text-transform: uppercase;
        letter-spacing: 0.5px; margin: 4px 0 8px 0; text-align: center;
    }
    /* Nút điều hướng trang: to, bo góc, dễ bấm */
    section[data-testid="stSidebar"] .stButton > button {
        font-size: 17px !important; font-weight: 900 !important;
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

# --- 2. DATABASE (ĐÃ CẬP NHẬT THEO YÊU CẦU CỦA HENRY) ---
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
    "Mia Bui": "Probation",
    "Niko Nguyen": "Probation",
    "Martin Tran": "Probation",
    "Ray Duong": "Probation",
    "Marky Huynh": "Probation"
}
STAFF_LIST = list(STAFF_CONFIG.keys())
LEVEL_TARGETS = {"GOLD": 9000, "SILVER": 9000, "BRONZE": 9000, "Associated": 9000, "Probation": 9000}  # 9000s = 2h30 cho tất cả
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
    """Trả về (date_from, date_to, n_days) dạng MM/DD/YYYY từ cột Date của file RingCentral."""
    if 'Date' not in df.columns:
        return (None, None, 0)
    s = pd.to_datetime(df['Date'].astype(str).str.strip(), format='%a %m/%d/%Y', errors='coerce').dropna()
    if len(s) == 0:
        return (None, None, 0)
    days = sorted(pd.Series(s.dt.normalize().unique()))
    dfrom = pd.Timestamp(days[0]).strftime('%m/%d/%Y')
    dto = pd.Timestamp(days[-1]).strftime('%m/%d/%Y')
    return (dfrom, dto, len(days))

@st.cache_data(ttl=10, show_spinner=False)
def _read_gsheet(url):
    return pd.read_csv(url)

import re
def _to_off(v):
    if pd.isna(v): return False
    return str(v).strip().lower() in ('true', '1', 'x', 'off', 'yes', 'có', 'co')

def _safe_num(v):
    """Chuyển ô Sheet sang số; rỗng/NaN -> 0 (tránh bug `NaN or 0` = NaN)."""
    n = pd.to_numeric(v, errors='coerce')
    return 0.0 if pd.isna(n) else float(n)

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

def gsheet_apply(url, date_from, date_to):
    """Nạp dữ liệu từ Google Sheet (published CSV). Tự nhận 2 format:
      • DỌC (cũ): cột Date, Sales Name, Chốt, OFF, Số P — mỗi dòng 1 người/ngày.
      • NGANG (mới, theo tháng): hàng = tên Sales; cột = ngày, mỗi ngày có Chốt/Giảm/OFF
        (tiêu đề kiểu '28 Chốt', '28 Giảm', '28 OFF').
    1 ngày -> Chốt + Giảm(P) + OFF; nhiều ngày -> chỉ CỘNG DỒN Chốt.
    Trả về số dòng đã nạp, hoặc -1 nếu lỗi đọc."""
    try:
        g = _read_gsheet(url).copy()
    except Exception as e:
        st.sidebar.error(f"Không đọc được Google Sheet: {e}")
        return -1
    g.columns = [str(c).strip() for c in g.columns]
    idf = st.session_state.input_df
    d0 = pd.to_datetime(date_from, errors='coerce'); d1 = pd.to_datetime(date_to, errors='coerce')
    single = (date_from == date_to)
    has_date = any(c.lower() in ('date', 'ngày', 'ngay') for c in g.columns)

    if has_date:
        # ---------- FORMAT DỌC (cũ) ----------
        colmap = {}
        for c in g.columns:
            cl = c.lower()
            if cl in ('date', 'ngày', 'ngay'): colmap[c] = 'Date'
            elif cl in ('sales name', 'name', 'tên', 'ten', 'sales', 'nhân viên', 'nhan vien'): colmap[c] = 'Sales Name'
            elif cl in ('chốt', 'chot', 'chốt $', 'premium'): colmap[c] = 'Chốt'
            elif cl == 'off' or 'xin off' in cl or cl in ('nghỉ', 'nghi'): colmap[c] = 'OFF'
            elif cl in ('số p', 'so p', 'giảm số p', 'giam so p', 'p', 'giảm talktime'): colmap[c] = 'Số P'
        g = g.rename(columns=colmap)
        if 'Sales Name' not in g.columns:
            return 0
        g['_d'] = pd.to_datetime(g['Date'].astype(str).str.strip(), errors='coerce')
        sel = g[(g['_d'] >= d0) & (g['_d'] <= d1)].copy()
        sel['_nm'] = sel['Sales Name'].astype(str).str.strip()
        n = 0
        if single:
            for nm in sel['_nm'].unique():
                if nm not in idf.index: continue
                r = sel[sel['_nm'] == nm].iloc[-1]
                if 'Chốt' in sel.columns:
                    idf.loc[nm, 'Chốt $'] = _safe_num(r.get('Chốt'))
                if 'OFF' in sel.columns:
                    idf.loc[nm, 'Xin OFF'] = _to_off(r.get('OFF'))
                if 'Số P' in sel.columns:
                    idf.loc[nm, 'Giảm số P'] = _safe_num(r.get('Số P'))
                n += 1
        else:
            if 'Chốt' in sel.columns:
                sel['_c'] = pd.to_numeric(sel['Chốt'], errors='coerce').fillna(0)
                for nm, val in sel.groupby('_nm')['_c'].sum().items():
                    if nm in idf.index: idf.loc[nm, 'Chốt $'] = float(val); n += 1
        return n

    # ---------- FORMAT NGANG (mới, theo tháng) ----------
    name_col = g.columns[0]
    for c in g.columns:
        if c.lower() in ('sales name', 'name', 'tên', 'ten', 'sales', 'nhân viên', 'nhan vien'):
            name_col = c; break
    # gom cột theo NGÀY: tiêu đề bắt đầu bằng số ngày + nhãn Chốt/Giảm/OFF
    daymap = {}
    for c in g.columns:
        if c == name_col: continue
        m = re.match(r'\s*(\d{1,2})', c)
        if not m: continue
        day = int(m.group(1)); cl = c.lower()
        if 'chốt' in cl or 'chot' in cl or 'premium' in cl: fld = 'Chốt'
        elif 'off' in cl or 'nghỉ' in cl or 'nghi' in cl: fld = 'OFF'
        elif 'giảm' in cl or 'giam' in cl or 'talktime' in cl or cl.strip().endswith(' p') or 'số p' in cl: fld = 'Giảm'
        else: continue
        daymap.setdefault(day, {})[fld] = c
    if not daymap:
        st.sidebar.warning("Google Sheet chưa đúng format (cần cột kiểu '28 Chốt', '28 OFF'…).")
        return 0
    if single:
        days = [d0.day]
    else:
        # Duyệt từng ngày thực trong CSV (tránh cộng nhầm cả tháng khi range nhiều ngày)
        days = []
        cur = d0.normalize()
        while cur <= d1.normalize():
            if cur.day in daymap:
                days.append(cur.day)
            cur += pd.Timedelta(days=1)
    n = 0
    for _, row in g.iterrows():
        nm = str(row[name_col]).strip()
        if nm not in idf.index: continue
        if single:
            f = daymap.get(days[0], {})
            if 'Chốt' in f:
                idf.loc[nm, 'Chốt $'] = _safe_num(row.get(f['Chốt']))
            if 'OFF' in f:
                idf.loc[nm, 'Xin OFF'] = _to_off(row.get(f['OFF']))
            if 'Giảm' in f:
                idf.loc[nm, 'Giảm số P'] = _safe_num(row.get(f['Giảm']))
        else:
            tot = sum(_safe_num(row.get(daymap.get(d, {}).get('Chốt'))) for d in days
                      if daymap.get(d, {}).get('Chốt'))
            idf.loc[nm, 'Chốt $'] = float(tot)
        n += 1
    return n

# --- 3. SESSION STATE ---
if 'input_df' not in st.session_state:
    st.session_state.input_df = pd.DataFrame({
        "Sales Name": STAFF_LIST, "Chốt $": 0.0, "Xin OFF": False, "Giảm số P": 0.0
    }).set_index("Sales Name")

def update_input():
    # Ghi theo TÊN (không theo vị trí) để tránh lệch dòng khi file RingCentral
    # không đủ 24 người. row_idx là vị trí trong bảng đang hiển thị (active_staff),
    # nên phải map ngược ra tên trước khi ghi.
    if "editor_v82" in st.session_state:
        active = st.session_state.get('active_staff', [])
        for row_idx, changes in st.session_state["editor_v82"]["edited_rows"].items():
            if row_idx >= len(active):
                continue
            name = active[row_idx]
            for k, v in changes.items():
                st.session_state.input_df.loc[name, k] = v

# --- 4. SIDEBAR ---
st.sidebar.markdown("# 💎 Master Dashboard")
uploaded_file = st.sidebar.file_uploader("📂 Tải file RingCentral", type=["csv"])

# --- LIÊN KẾT GOOGLE SHEET NHẬP LIỆU (Chốt / OFF / Số P theo ngày) ---
# Link CSV published mặc định (gắn cứng) — dữ liệu tự cập nhật gần realtime.
DEFAULT_GSHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTv1WZPG26RYVV4p1e3CuTW59OcLH18udmg0FvE_IaNZn8B0S7Ki0TzD5ENxDbWolGL7y42kn7PsHcA/pub?output=csv"
_default_gs = DEFAULT_GSHEET_URL
try:
    _default_gs = st.secrets.get("GSHEET_CSV_URL", DEFAULT_GSHEET_URL)
except Exception:
    _default_gs = DEFAULT_GSHEET_URL
with st.sidebar.expander("🔗 Google Sheet nhập liệu", expanded=False):
    gs_url = st.text_input("Link CSV published của Google Sheet",
                           value=st.session_state.get("gsheet_url", _default_gs),
                           help="Đã gắn sẵn link. Đổi link khác thì dán vào đây.")
    st.session_state["gsheet_url"] = gs_url
    if st.button("🔄 Đồng bộ lại từ Google Sheet", use_container_width=True):
        st.session_state.pop("gs_synced", None)
        _read_gsheet.clear()
        st.rerun()
    st.caption("Nhập Chốt/OFF/Số P theo NGÀY trên Google Sheet — web tự lấy đúng range ngày trong file CSV. Tự cập nhật ~10 giây/lần.")

# Thư mục lưu dữ liệu Final theo ngày (nằm cạnh file .py)
HISTORY_DIR = "history"
os.makedirs(HISTORY_DIR, exist_ok=True)

# --- ĐIỀU HƯỚNG TRANG (luôn hiện, nút to dễ bấm) ---
if 'page' not in st.session_state:
    st.session_state.page = "📊 Báo cáo & Biểu đồ"
st.sidebar.markdown("---")
st.sidebar.markdown('<div class="nav-title">📄 Chọn trang</div>', unsafe_allow_html=True)
_nav = [("📝 Nhập doanh số & Điều chỉnh", "📝  NHẬP DOANH SỐ"),
        ("📊 Báo cáo & Biểu đồ", "📊  BÁO CÁO & BIỂU ĐỒ"),
        ("📅 Lịch sử", "📅  LỊCH SỬ (NGÀY CŨ)")]
for _val, _label in _nav:
    if st.sidebar.button(_label, use_container_width=True,
                         type=("primary" if st.session_state.page == _val else "secondary")):
        st.session_state.page = _val; st.rerun()
page = st.session_state.page

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
    df_raw.columns = df_raw.columns.str.strip()

    # KHOẢNG NGÀY của báo cáo (để link Google Sheet + hiển thị range nếu chạy theo tháng)
    date_from, date_to, n_days = extract_report_range(df_raw)
    is_range = bool(date_from and date_to and date_from != date_to)
    report_date = date_from                                   # dùng cho khớp 1 ngày
    if date_from:
        if is_range:
            file_date = f"{date_from.replace('/','-')}_den_{date_to.replace('/','-')}"
            static_time = f"{date_from} → {date_to}  ({n_days} ngày) | {now.strftime('%H:%M')}"
        else:
            file_date = date_from.replace('/', '-')
            static_time = f"{date_from} | {now.strftime('%H:%M')}"

    # --- BƯỚC LỌC 1: CHỈ GIỮ OUTGOING — XÓA THẲNG MỌI DÒNG INCOMING ---
    n_incoming = 0
    if 'Direction' in df_raw.columns:
        _dir = df_raw['Direction'].astype(str).str.strip().str.lower()
        n_incoming = int((_dir == 'incoming').sum())
        df_raw = df_raw[_dir == 'outgoing']          # bỏ Incoming + mọi dòng không phải Outgoing
        if n_incoming:
            st.sidebar.caption(f"🚫 Đã loại {n_incoming} dòng Incoming khỏi talktime.")
    else:
        st.warning("⚠️ Không tìm thấy cột 'Direction'. Vui lòng kiểm tra lại định dạng file.")

    # --- ĐÁNH DẤU DÒNG TRANSFER (KHÔNG bỏ) — dùng làm tín hiệu nhận diện chuỗi transfer ---
    if 'Action' in df_raw.columns:
        df_raw['is_tr'] = df_raw['Action'].astype(str).str.strip().str.lower() == 'transfer'
    elif 'Type' in df_raw.columns:   # dự phòng: Type trống ~ Transfer
        df_raw['is_tr'] = df_raw['Type'].astype(str).str.strip().str.lower() != 'voice'
    else:
        df_raw['is_tr'] = False

    # RingCentral: thường là "Ext - Tên" hoặc đôi khi "Tên - Ext"
    df_raw['Ext_Name'] = df_raw['Extension'].apply(_parse_ext_name)
    df_raw['Sec'] = df_raw['Duration'].apply(to_seconds)
    df_raw['Start'] = pd.to_datetime(
        df_raw['Date'].astype(str).str.strip() + ' ' + df_raw['Time'].astype(str).str.strip(),
        format='%a %m/%d/%Y %I:%M %p', errors='coerce')
    df_raw = df_raw.dropna(subset=['Start'])
    df_raw['End'] = df_raw['Start'] + pd.to_timedelta(df_raw['Sec'], unit='s')

    # BÁO CÁO TẤT CẢ nhân viên theo đúng thứ tự STAFF_LIST (không lọc bỏ ai).
    active_in_file = df_raw['Ext_Name'].unique()
    active_staff = list(STAFF_LIST)
    no_data_staff = [n for n in active_staff if n not in active_in_file]
    NO_DATA_SET = set(no_data_staff)

    # TÍNH TALKTIME theo TÍN HIỆU TRANSFER:
    # - Gom các dòng chồng thời gian thành 1 cụm.
    # - Cụm CÓ dòng Transfer  = chuỗi transfer (cùng 1 cuộc bị chuyển máy) -> tính 1 cuộc = leg DÀI NHẤT.
    # - Cụm KHÔNG Transfer     = các cuộc gọi RIÊNG BIỆT (khác khách) -> CỘNG ĐỦ từng cuộc.
    # Dòng Transfer chỉ dùng để nhận diện, KHÔNG cộng duration.
    def _agg_calls(g):
        """Tính talktime: Transfer = tín hiệu nối chuỗi (không cộng duration).
        Cuộc chồng thời gian trong chuỗi transfer -> 1 cuộc (leg dài nhất).
        Cuộc riêng (không transfer) -> cộng đủ từng cuộc."""
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

    # --- LIÊN KẾT GOOGLE SHEET (REALTIME): mỗi lần chạy tự lấy đúng range ngày ---
    # 1 ngày -> Chốt/OFF/Số P; nhiều ngày -> cộng dồn Chốt. Đọc qua cache 10s.
    _gs = st.session_state.get("gsheet_url", "").strip()
    if _gs and date_from:
        # reset về mặc định trước khi nạp -> phản ánh đúng cả khi Sheet bị xoá dòng
        st.session_state.input_df.loc[active_staff, ['Chốt $', 'Xin OFF', 'Giảm số P']] = [0.0, False, 0.0]
        _n = gsheet_apply(_gs, date_from, date_to)
        if _n >= 0:
            _lbl = (f"{date_from}→{date_to} (cộng dồn Chốt)" if is_range else f"ngày {date_from}")
            st.sidebar.caption(f"🔗 Google Sheet: đã nạp {_n} dòng — {_lbl}")

    current_input_display = st.session_state.input_df.loc[active_staff]

    # --- TÍNH TOÁN (chạy chung cho cả 2 trang) ---
    final_df = pd.concat([current_input_display, stats], axis=1).fillna(0).reset_index()
    final_df.rename(columns={'index': 'Sales Name'}, inplace=True)

    _days_mult = n_days if (is_range and n_days > 0) else 1
    def calculate_metrics(row):
        name = row['Sales Name']; lvl = STAFF_CONFIG.get(name, "Probation")
        target_orig = LEVEL_TARGETS.get(lvl, 9000) * _days_mult   # theo THÁNG: mục tiêu × số ngày
        actual = row['Actual_Sec']
        giam_p = float(row['Giảm số P'])
        if row['Xin OFF']:
            return pd.Series([lvl, target_orig, giam_p, actual, actual, 0.0, "OFF"])
        sales = row['Chốt $']
        if name in NO_DATA_SET and sales == 0:
            return pd.Series([lvl, target_orig, giam_p, 0, 0, 0.0, "NO DATA"])
        if is_range:
            # THEO THÁNG: goal = 2h30 × số ngày; Chốt chỉ hiển thị (không trừ bonus, không Giảm P)
            goal = target_orig
            total = actual
            pct = 100.0 if goal <= 0 else total / goal * 100
            return pd.Series([lvl, goal, 0.0, actual, total, round(float(pct), 1),
                              "GOOD JOB" if pct >= 100 else "COME ON!"])
        # --- 1 NGÀY: rule cũ (bonus theo Chốt, +Giảm P vào Total) ---
        is_done = sales >= 2000
        bonus = 1800 if 300 <= sales < 500 else (2700 if 500 <= sales < 1000 else (5400 if 1000 <= sales < 2000 else 0))
        goal = 0 if is_done else max(0, target_orig - bonus)
        total = actual + giam_p * 60
        pct = 100.0 if (is_done or goal <= 0) else total / goal * 100
        return pd.Series([lvl, goal, giam_p, actual, total, round(float(pct), 1),
                          "GOOD JOB" if (pct >= 100 or is_done) else "COME ON!"])

    final_df[['🏅 LVL', 'goal_val', 'giam_p', 'actual_val', 'total_val', 'pct_val', '📊 RESULT']] = final_df.apply(calculate_metrics, axis=1)
    # % lấy CỘT CAO NHẤT làm tham chiếu (để so sánh tương đối giữa các bạn)
    _vv = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])]
    max_pct = float(_vv['pct_val'].max()) if len(_vv) and _vv['pct_val'].max() > 0 else 100.0
    # GIỮ THỨ TỰ CỐ ĐỊNH theo STAFF_LIST (không sort theo hiệu suất)
    final_df = final_df.reset_index(drop=True)

# ==================== TRANG 1: NHẬP LIỆU ====================
if uploaded_file and page == "📝 Nhập doanh số & Điều chỉnh":
    st.subheader("📝 BẢNG NHẬP DOANH SỐ & ĐIỀU CHỈNH")
    st.caption("Nhập xong, chuyển sang trang **📊 Báo cáo & Biểu đồ** ở thanh bên để xem kết quả.")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.data_editor(current_input_display, use_container_width=True, key="editor_v82",
                       on_change=update_input, height=((len(active_staff)*35)+40))

# ==================== TRANG 2: BÁO CÁO ====================
if uploaded_file and page == "📊 Báo cáo & Biểu đồ":
    # (Tiêu đề + KPI được hiển thị trong khối bảng HTML bên dưới — không lặp lại ở đây)
    t_p = int(final_df['Chốt $'].sum())
    t_t = format_time(final_df['Actual_Sec'].sum())
    t_c = int(final_df['Tong_Cuoc_Goi'].sum())
    _valid = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])]
    team_pct = round(_valid['total_val'].sum() / _valid['goal_val'].sum() * 100, 1) if _valid['goal_val'].sum() > 0 else 0.0
    n_done = int((final_df['📊 RESULT'] == "GOOD JOB").sum())
    n_active = int(len(_valid))

    # --- 8. BẢNG (dữ liệu để export CSV; bảng hiển thị là HTML bên dưới) ---
    valid = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])]
    tot_goal = valid['goal_val'].sum()
    tot_total = valid['total_val'].sum()
    tot_pct = round(tot_total / tot_goal * 100, 1) if tot_goal > 0 else 0.0

    def _nd(r, v):  # "—" nếu NO DATA
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

    # --- GHI CHÚ: nhân viên không có dữ liệu talktime ---
    if no_data_staff:
        st.warning(f"📝 **Không có dữ liệu talktime ({len(no_data_staff)}):** " + " • ".join(no_data_staff))

    # ================= CHẾ ĐỘ TOÀN MÀN HÌNH (tiêu đề + KPI + bảng cùng lúc) =================
    def _bar_green(pct, label):   # Total so với GOAL — xanh nhạt
        p = max(0, min(pct, 100))
        return (f'<div class="pbar"><div class="pfill" style="width:{p:.0f}%;background:#A7D8B0;"></div>'
                f'<span style="color:#1E5631;">{label}</span></div>')

    def _bar_pct(rel_w, real_pct, label):   # % — dài so với cột cao nhất; màu theo ngưỡng
        p = max(0, min(rel_w, 100))
        if real_pct >= 100: fill, txt = "#EF4444", "#ffffff"
        else:               fill, txt = "#FDE68A", "#7A5B00"
        return (f'<div class="pbar"><div class="pfill" style="width:{p:.0f}%;background:{fill};"></div>'
                f'<span style="color:{txt};">{label}</span></div>')

    rows_html = ""
    for _, r in final_df.iterrows():
        res = r['📊 RESULT']; lvl = r['🏅 LVL']
        s5, s10, s30 = int(r["Int_5p"]), int(r["Int_10p"]), int(r["Int_30p"])
        if res == "NO DATA":
            rows_html += (f'<tr class="nod"><td>{r["Sales Name"]}</td><td>{lvl}</td>'
                          f'<td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td>'
                          f'<td>0</td><td>{s5}</td><td>{s10}</td><td>{s30}</td><td>{s5+s10+s30}</td>'
                          f'<td class="badge nodb">NO DATA</td></tr>')
            continue
        lvl_bg = LEVEL_COLORS.get(lvl, "#FFFFFF"); lvl_tx = LEVEL_TEXT.get(lvl, "#12326B")
        chot = f"${int(r['Chốt $']):,}" if r['Chốt $'] > 0 else "$0"
        _c = r['Chốt $']
        if _c >= 300:   chot_style = 'style="background:#F87171;color:#7F1D1D;"'   # ĐỎ (≥$300)
        elif _c >= 100: chot_style = 'style="background:#FDBA74;color:#7C2D12;"'   # CAM ($100–300)
        elif _c >= 1:   chot_style = 'style="background:#FDE68A;color:#854D0E;"'   # VÀNG ($1–100)
        else:           chot_style = ''
        total_bar = _bar_green(r['total_val'] / r['goal_val'] * 100 if r['goal_val'] > 0 else 100,
                               format_time(r['total_val']))
        pct_bar = _bar_pct(r['pct_val'] / max_pct * 100, r['pct_val'], f"{r['pct_val']:.0f}%")
        if res == "GOOD JOB": badge = '<td class="badge okb">GOOD JOB</td>'
        elif res == "OFF":    badge = '<td class="badge offb">OFF</td>'
        else:                 badge = '<td class="badge cmb">COME ON!</td>'
        rows_html += (f'<tr><td>{r["Sales Name"]}</td>'
                      f'<td style="background:{lvl_bg};color:{lvl_tx};">{lvl}</td>'
                      f'<td {chot_style}>{chot}</td>'
                      f'<td>{format_time(r["goal_val"])}</td>'
                      f'<td>{int(r["giam_p"])}p</td>'
                      f'<td>{format_time(r["actual_val"])}</td>'
                      f'<td>{total_bar}</td><td>{pct_bar}</td>'
                      f'<td>{int(r["Tong_Cuoc_Goi"])}</td>'
                      f'<td>{s5}</td><td>{s10}</td><td>{s30}</td><td><b>{s5+s10+s30}</b></td>'
                      f'{badge}</tr>')
    T5, T10, T30 = int(final_df["Int_5p"].sum()), int(final_df["Int_10p"].sum()), int(final_df["Int_30p"].sum())
    rows_html += (f'<tr class="tot"><td>TOTAL</td><td></td>'
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
        <div class="kpi"><div class="ic" style="background:#FCEFCF;">🏆</div><div class="lb">Đạt mục tiêu</div><div class="vl">{n_done}<span style="font-size:20px;color:#94A3B8;">/{n_active}</span></div></div>
      </div>"""

    n_rows = len(final_df) + 1
    box_h = 250 + n_rows * 52 + 80
    full_html = f"""
    <div id="reportBox" class="wrap">
      <button class="fsbtn" onclick="goFS()">⛶ Toàn màn hình</button>
      <div class="title">🏆 WORKING RESULTS STATISTICS | {static_time} (EST)</div>
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
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
      * {{ box-sizing:border-box; font-family:'Inter','Segoe UI',Roboto,Arial,sans-serif; }}
      body {{ margin:0; }}
      .wrap {{ padding:16px; background:#F6F9FF; position:relative; }}
      #reportBox:fullscreen {{ overflow:auto; }}
      .fsbtn {{ position:absolute; right:18px; top:18px; z-index:9; background:#fff; color:#33507A;
                border:1px solid #CBD8EC; border-radius:10px; padding:9px 15px; font-weight:600;
                font-size:14px; cursor:pointer; box-shadow:0 2px 6px rgba(30,58,138,.12); }}
      .fsbtn:hover {{ background:#EEF4FF; }}
      .title {{ background:linear-gradient(135deg,#0F2A5B,#1E40AF); color:#fff; text-align:center;
                font-weight:700; font-size:26px; padding:18px; border-radius:14px; letter-spacing:.3px; }}
      .kpis {{ display:flex; gap:14px; margin:16px 0; flex-wrap:wrap; }}
      .kpi {{ flex:1; min-width:168px; text-align:center; background:#fff; border:1px solid #E6ECF5;
              border-radius:16px; padding:16px; box-shadow:0 6px 16px rgba(30,58,138,.07); }}
      .kpi .ic {{ width:48px;height:48px;border-radius:14px;margin:0 auto 8px;display:flex;
                  align-items:center;justify-content:center;font-size:23px; }}
      .kpi .lb {{ font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#7A8AA0; }}
      .kpi .vl {{ font-size:35px;font-weight:800;color:#1B3B72; }}
      table {{ width:100%; border-collapse:separate; border-spacing:0 6px; }}
      th {{ font-size:16.5px; font-weight:900; color:#5A6B85; text-align:center; padding:7px 5px;
            text-transform:uppercase; letter-spacing:.2px; }}
      td {{ font-size:16.5px; font-weight:900; text-align:center; padding:9px 5px; background:#fff; color:#1A2337; }}
      tr td:first-child {{ border-radius:12px 0 0 12px; }}
      tr td:last-child  {{ border-radius:0 12px 12px 0; }}
      tr.nod td {{ background:#F3F6FB; color:#AEB8C6; font-weight:800; }}
      tr.tot td {{ background:#33507A; color:#fff; font-weight:800; font-size:17.5px; }}
      .pbar {{ position:relative; height:22px; background:#EEF2F8; border-radius:7px; overflow:hidden; }}
      .pfill {{ position:absolute; left:0; top:0; bottom:0; }}
      .pbar span {{ position:relative; z-index:2; line-height:22px; font-weight:900; font-size:14.5px; }}
      .badge {{ border-radius:10px; font-weight:900; }}
      .okb {{ background:#DCFCE7; color:#166534; }}
      .cmb {{ background:#FEE2E2; color:#B91C1C; }}
      .offb {{ background:#E2E8F0; color:#475569; }}
      .nodb {{ background:#EEF2F8; color:#94A3B8; }}
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

    st.markdown("#### 📋 Bảng kết quả")
    components.html(full_html, height=box_h, scrolling=True)

    # --- COPY CỘT % ĐỂ DÁN SANG GOOGLE SHEET ---
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

    # --- 9. BIỂU ĐỒ (phân nhóm trạng thái + đường mục tiêu 100%) ---
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

    # --- 9b. BIỂU ĐỒ ĐƯỜNG: CUỘC GỌI CHẤT LƯỢNG (≥5 PHÚT = 5p + 10p + 30p) ---
    line_df = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])].copy()
    if len(line_df):
        line_df['Interest'] = line_df['Int_5p'] + line_df['Int_10p'] + line_df['Int_30p']
        tot_5p = int((final_df['Int_5p'] + final_df['Int_10p'] + final_df['Int_30p']).sum())
        st.markdown(f'<div class="main-header">📈 CUỘC GỌI CHẤT LƯỢNG ≥5 PHÚT | TỔNG: {tot_5p} CUỘC</div>', unsafe_allow_html=True)
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

    # --- 10. SNAPSHOT (dạng số + có cột Date) ---
    snapshot = final_df[['Sales Name', '🏅 LVL', 'Xin OFF', 'Chốt $',
                         'goal_val', 'giam_p', 'actual_val', 'total_val', 'pct_val',
                         'Tong_Cuoc_Goi', 'Int_5p', 'Int_10p', 'Int_30p', '📊 RESULT']].copy()
    snapshot.insert(0, 'Date', file_date)

    # --- 11. LƯU / EXPORT ---
    st.markdown("---")
    cc1, cc2, cc3 = st.columns([1.4, 1, 1])
    with cc1:
        # LƯU DỮ LIỆU FINAL CỦA NGÀY -> đọc lại được ở trang Lịch sử
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

        # KPI của ngày đã lưu
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

        # Bảng ngày đã lưu (định dạng lại thời gian)
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
