
import streamlit as st
import easyocr
from PIL import Image
import fitz
import io

st.set_page_config(page_title="QuantumDocs: EasyOCR Edition", layout="wide")
st.title("🔷 QuantumDocs with EasyOCR")

ocr_reader = easyocr.Reader(['en'], gpu=False)

uploaded_files = st.file_uploader("📁 Upload PDF or Image documents", type=["pdf", "png", "jpg", "jpeg", "tif"], accept_multiple_files=True)

def extract_text_from_image(img: Image.Image) -> str:
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    results = ocr_reader.readtext(img_bytes.read(), detail=0, paragraph=True)
    return "\n".join(results)

def extract_text(file):
    text = ""
    if file.type == "application/pdf":
        st.info(f"OCR: Processing PDF - {file.name}")
        pdf_bytes = file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text += extract_text_from_image(img) + "\n"
    else:
        st.info(f"OCR: Processing Image - {file.name}")
        img = Image.open(file)
        text = extract_text_from_image(img)
    return text

if uploaded_files:
    uploaded_files = sorted(uploaded_files, key=lambda x: x.name.lower())
    for file in uploaded_files:
        st.header(f"📄 {file.name}")
        try:
            extracted_text = extract_text(file)
            st.text_area("📝 OCR Text", extracted_text, height=300)
        except Exception as e:
            st.error(f"OCR failed for {file.name}: {e}")
else:
    st.info("Upload your PDF or image files to begin.")
