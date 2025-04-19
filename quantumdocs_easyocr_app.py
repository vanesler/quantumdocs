import streamlit as st
import easyocr
from PIL import Image
import io

st.set_page_config(page_title="QuantumDocs: EasyOCR", layout="wide")
st.title("🔷 QuantumDocs (Streamlit Cloud Ready)")

ocr_reader = easyocr.Reader(['en'], gpu=False)

uploaded_files = st.file_uploader("📁 Upload an image or PDF file", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

def extract_text_from_image(img: Image.Image) -> str:
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    results = ocr_reader.readtext(img_bytes.getvalue(), detail=0, paragraph=True)
    return "\n".join(results)

if uploaded_files:
    for file in uploaded_files:
        st.header(f"📄 {file.name}")
        try:
            img = Image.open(file)
            text = extract_text_from_image(img)
            st.text_area("📝 OCR Result", text, height=300)
        except Exception as e:
            st.error(f"Error processing file: {e}")
else:
    st.info("Upload an image file to begin.")