
import streamlit as st
from paddleocr import PaddleOCR
from PIL import Image
import io
import fitz
import os

st.set_page_config(page_title="QuantumDocs: PaddleOCR Edition", layout="wide")
st.title("🔷 QuantumDocs with PaddleOCR")

ocr = PaddleOCR(use_angle_cls=True, lang='en')

uploaded_files = st.file_uploader("📁 Upload documents (PDF or image)", type=["pdf", "png", "jpg", "jpeg", "tif"], accept_multiple_files=True)

def extract_text_from_image(img: Image.Image) -> str:
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_array = img_bytes.getvalue()
    result = ocr.ocr(img_array, cls=True)
    lines = []
    for line in result[0]:
        lines.append(line[1][0])
    return "\n".join(lines)

def extract_text(file):
    text = ""
    if file.type == "application/pdf":
        doc = fitz.open(stream=file.read(), filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text += extract_text_from_image(img) + "\n"
    else:
        img = Image.open(file)
        text = extract_text_from_image(img)
    return text

if uploaded_files:
    for file in uploaded_files:
        st.header(f"📄 {file.name}")
        try:
            ocr_text = extract_text(file)
            st.text_area("Extracted Text", ocr_text, height=300)
        except Exception as e:
            st.error(f"OCR error: {e}")
else:
    st.info("Upload PDFs or images to begin.")
