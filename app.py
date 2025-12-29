import base64
from pathlib import Path

import streamlit as st
from rag import create_qa_chain


# ============================================================
# 1) KLASÖR/YOL AYARLARI
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR.mkdir(exist_ok=True)


# ============================================================
# 2) YARDIMCI FONKSİYON
# ============================================================
def file_to_b64(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


# ============================================================
# 3) STREAMLIT SAYFA AYARLARI
# ============================================================
st.set_page_config(
    page_title="Mitoloji Ansiklopedisi (Gemini)",
    page_icon="🏛️",
    layout="centered",
)

bg_b64 = file_to_b64(ASSETS_DIR / "bg.jpg")
logo_b64 = file_to_b64(ASSETS_DIR / "logo.png")


# ============================================================
# 4) YAN PANEL (DB SIFIRLAMA YOK)
# ============================================================
with st.sidebar:
    st.header("⚙️ Ayarlar")

    theme = st.radio("🎨 Tema", ["🌙 Koyu", "☀️ Açık"], index=0)

    st.markdown("---")
    st.subheader("🧯 Bakım")

    if st.button("🧹 Sohbeti Temizle"):
        st.session_state.messages = []


# ============================================================
# 5) CSS / GÖRÜNÜM
# ============================================================
overlay = "rgba(0,0,0,.65)" if theme == "🌙 Koyu" else "rgba(255,255,255,.55)"
card_bg = "rgba(255,255,255,0.10)" if theme == "🌙 Koyu" else "rgba(255,255,255,0.75)"
text_color = "#f5f5f5" if theme == "🌙 Koyu" else "#111111"

st.markdown(
    f"""
    <style>
    /* Tüm sayfanın arka planı */
    .stApp {{
        background: linear-gradient({overlay}, {overlay}),
                    url("data:image/jpg;base64,{bg_b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: {text_color};
    }}

    /* ÜST BAR (Streamlit header) */
    header[data-testid="stHeader"] {{
        background: #0b1c3d !important;
    }}

    /* YAN BAR (Sidebar) */
    section[data-testid="stSidebar"] {{
        background: #0b1c3d !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: #ffffff !important;
    }}

    /* Sayfanın altındaki varsayılan beyaz alanlar */
    footer {{
        background: #0b1c3d !important;
    }}
    div[data-testid="stBottomBlockContainer"] {{
        background: #0b1c3d !important;
    }}

    /* İçerik kartı */
    .card {{
        background: {card_bg};
        border: 1px solid rgba(212,175,55,0.40);
        box-shadow: 0 10px 35px rgba(0,0,0,0.45);
        backdrop-filter: blur(10px);
        border-radius: 18px;
        padding: 22px;
        margin-top: 18px;
    }}

    /* Altın çizgi */
    .goldline {{
        height: 2px;
        background: linear-gradient(90deg, rgba(212,175,55,0),
                                    rgba(212,175,55,1),
                                    rgba(212,175,55,0));
        margin: 10px 0 18px 0;
    }}

    /* BUTONLAR (tümü lacivert) */
    div.stButton > button {{
        background-color: #0b1c3d !important;
        color: #ffffff !important;
        border: 1px solid #1f3c88 !important;
        border-radius: 10px !important;
        padding: 0.45rem 0.8rem !important;
        font-weight: 600 !important;
    }}
    div.stButton > button:hover {{
        background-color: #142b5f !important;
        color: #ffffff !important;
        border-color: #2f5fd0 !important;
    }}
    div.stButton > button:active {{
        background-color: #09152e !important;
        color: #ffffff !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 6) ÜST BAŞLIK
# ============================================================
st.markdown('<div class="card">', unsafe_allow_html=True)

col1, col2 = st.columns([1, 5])
with col1:
    if logo_b64:
        st.image(f"data:image/png;base64,{logo_b64}", width=64)
    else:
        st.write("🏛️")

with col2:
    st.title("Mitoloji Ansiklopedisi Ajanı")
    if st.session_state.get("user_name"):
        st.caption(f"Hoş geldin, **{st.session_state.user_name}** ⚡")
    else:
        st.caption("Gemini API + RAG • Yunan Mitolojisi")

st.markdown('<div class="goldline"></div>', unsafe_allow_html=True)


# ============================================================
# 7) ÖRNEK / HAZIR SORULAR
# ============================================================
st.subheader("💡 Örnek Sorular")
examples = [
    "Zeus kimdir?",
    "Athena neyin tanrıçasıdır?",
    "Troya Savaşı nedir?",
    "Olympos tanrıları kimlerdir?",
    "Hades yeraltı dünyasını nasıl yönetirdi?",
]
cols = st.columns(len(examples))
for c, ex in zip(cols, examples):
    if c.button(ex):
        st.session_state.pending_q = ex

st.subheader("⚡ Hazır Sorular")
c1, c2, c3, c4, c5, c6 = st.columns(6)
if c1.button("Zeus"):
    st.session_state.pending_q = "Zeus kimdir?"
if c2.button("Hera"):
    st.session_state.pending_q = "Hera kimdir?"
if c3.button("Athena"):
    st.session_state.pending_q = "Athena kimdir?"
if c4.button("Poseidon"):
    st.session_state.pending_q = "Poseidon kimdir?"
if c5.button("Apollon"):
    st.session_state.pending_q = "Apollon kimdir?"
if c6.button("Artemis"):
    st.session_state.pending_q = "Artemis kimdir?"


# ============================================================
# 8) RAG ZİNCİRİ (CACHE)
# ============================================================
@st.cache_resource
def get_chain():
    return create_qa_chain()

qa = get_chain()


# ============================================================
# 9) CHAT
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

q = st.chat_input("Sorunu yaz...")

if (not q) and ("pending_q" in st.session_state):
    q = st.session_state.pending_q
    del st.session_state.pending_q

if q:
    st.session_state.messages.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner("🏛️ Olimpos'tan cevap getiriliyor..."):
            ans = qa(q)
        st.markdown(ans)

    st.session_state.messages.append({"role": "assistant", "content": ans})

st.markdown("</div>", unsafe_allow_html=True)


