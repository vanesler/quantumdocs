
import streamlit as st
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import fitz
import io
import pandas as pd
import os
import json
from openai import OpenAI
from openpyxl import load_workbook
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="QuantumDocs: Sorted OCR", layout="wide")
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-..."))

st.title("🔷 QuantumDocs: Sorted OCR by Filename")

uploaded_files = st.file_uploader("📁 Upload documents (processed in filename order)", type=["pdf", "png", "jpg", "jpeg", "tif"], accept_multiple_files=True)

def extract_text(file):
    try:
        if file.type == "application/pdf":
            st.info(f"OCR: Processing PDF: {file.name}")
            text = ""
            doc = fitz.open(stream=file.read(), filetype="pdf")
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                cleaned = ImageOps.invert(img.convert("RGB"))
                text += pytesseract.image_to_string(cleaned) + "\n"
            return text
        else:
            st.info(f"OCR: Processing Image: {file.name}")
            img = Image.open(file)
            cleaned = ImageOps.invert(img.convert("RGB"))
            return pytesseract.image_to_string(cleaned)
    except Exception as e:
        st.error(f"OCR error on {file.name}: {e}")
        return ""

if uploaded_files:
    st.success("✅ Files received — starting OCR process.")
    uploaded_files = sorted(uploaded_files, key=lambda x: x.name.lower())
    progress = st.progress(0)
    results = []

    for i, file in enumerate(uploaded_files):
        st.header(f"📄 {file.name}")
        ocr_text = extract_text(file)
        st.text_area("OCR Text", ocr_text, height=200, key=f"ocr_{file.name}")
        progress.progress((i + 1) / len(uploaded_files))

    st.success("🎉 OCR completed for all files!")
else:
    st.info("Upload document(s) to begin.")
