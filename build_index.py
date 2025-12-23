# Metin temizlemek için regex
import re
from pathlib import Path

# PDF ve TXT okumak için loader'lar
from langchain_community.document_loaders import PyPDFLoader, TextLoader

# Metni parçalara ayırmak için
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Embedding modeli
from langchain_community.embeddings import HuggingFaceEmbeddings

# FAISS: hızlı vektör veritabanı
from langchain_community.vectorstores import FAISS


# Bu dosyanın bulunduğu klasör
BASE = Path(__file__).resolve().parent

# Belgelerin olduğu klasör
DATA = BASE / "data"

# Oluşturulacak index klasörü
INDEX_DIR = BASE / "faiss_index"


def clean_text(t: str) -> str:
    """
    PDF'ten gelen bozuk satırları düzeltir:
    in-\nsan -> insan
    tanr ı -> tanrı gibi
    """
    t = t.replace("\r", "\n")
    t = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", t)
    t = re.sub(r"\n+", "\n", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"(\w)\s+([ıİiIüÜöÖşŞğĞçÇ])", r"\1\2", t)
    return t.strip()


# -------------------------------------------------
# 1) Belgeleri oku
# -------------------------------------------------
docs = []

for p in DATA.iterdir():
    if p.suffix.lower() == ".pdf":
        docs.extend(PyPDFLoader(str(p)).load())
    elif p.suffix.lower() == ".txt":
        docs.extend(TextLoader(str(p), encoding="utf-8").load())

if not docs:
    raise RuntimeError("❌ data/ içinde pdf veya txt bulunamadı.")


# -------------------------------------------------
# 2) Metni temizle
# -------------------------------------------------
for d in docs:
    d.page_content = clean_text(d.page_content)


# -------------------------------------------------
# 3) Metni parçalara böl
# -------------------------------------------------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=900,      # her parça ~900 karakter
    chunk_overlap=150   # parçalar arası 150 karakter örtüşme
)

chunks = [c for c in splitter.split_documents(docs) if c.page_content.strip()]


# -------------------------------------------------
# 4) Embedding modeli yükle
# -------------------------------------------------
# ✅ Çok kaliteli, çok dilli model
emb = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-base"
)


# -------------------------------------------------
# 5) FAISS index oluştur
# -------------------------------------------------
db = FAISS.from_documents(chunks, emb)

# klasörü oluştur
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# diske kaydet
db.save_local(str(INDEX_DIR))

print("✅ FAISS index oluşturuldu:", INDEX_DIR)
