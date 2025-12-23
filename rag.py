import os
from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI


# Proje dizini
BASE_DIR = Path(__file__).resolve().parent

# build_index.py'nin ürettiği klasör
INDEX_DIR = BASE_DIR / "faiss_index"


def _get_google_api_key():
    """
    API key'i önce ortam değişkeninden,
    yoksa Streamlit secrets'tan al.
    """
    key = os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        return None


def create_qa_chain():
    # -------------------------------------------------
    # 1) Index var mı kontrol et
    # -------------------------------------------------
    if not INDEX_DIR.exists():
        raise RuntimeError("❌ faiss_index/ yok. Önce: py build_index.py")


    # -------------------------------------------------
    # 2) Embedding modelini yükle
    # ⚠️ build_index.py ile AYNI olmak zorunda
    # -------------------------------------------------
    embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-base"
    )


    # -------------------------------------------------
    # 3) FAISS index'i yükle
    # -------------------------------------------------
    db = FAISS.load_local(
        str(INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )

    # Benzer parçaları getirecek retriever
    retriever = db.as_retriever(search_kwargs={"k": 8})


    # -------------------------------------------------
    # 4) Gemini LLM
    # -------------------------------------------------
    api_key = _get_google_api_key()
    if not api_key:
        raise RuntimeError("❌ GOOGLE_API_KEY yok.")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.2,
        google_api_key=api_key,
    )


    # -------------------------------------------------
    # 5) Asıl cevap fonksiyonu
    # -------------------------------------------------
    def answer(question: str) -> str:
        # a) Soruya benzer parçaları getir
        docs = retriever.invoke(question)

        # b) Hepsini tek bağlam metni yap
        context = "\n\n".join(d.page_content for d in docs)

        # c) Prompt
        prompt = f"""Sen bir mitoloji ansiklopedisi asistanısın.
SADECE aşağıdaki BAĞLAM'a dayanarak cevap ver.
- BAĞLAMDA yoksa: "Bilmiyorum." yaz.
- Türkçe, düzgün yaz.

BAĞLAM:
{context}

SORU:
{question}

CEVAP:
"""

        # d) Gemini'den cevap al
        return llm.invoke(prompt).content

    return answer
