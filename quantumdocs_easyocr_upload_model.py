import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageOps
import io
import openai
import pandas as pd
import easyocr
import numpy as np
import os
import json

st.set_page_config(page_title="QuantumDocs OCR - Upload Models", layout="wide")
st.title("📄 QuantumDocs OCR (Upload Model Files)")

# Upload model files if needed
st.subheader("🔧 Upload EasyOCR Model Files (once)")
craft_model = st.file_uploader("Upload craft_mlt_25k.pth", type=["pth"], key="craft")
lang_model = st.file_uploader("Upload english_g2.pth", type=["pth"], key="lang")

model_path = "/tmp/easyocr_models"
os.makedirs(model_path, exist_ok=True)

if craft_model and lang_model:
    with open(os.path.join(model_path, "craft_mlt_25k.pth"), "wb") as f:
        f.write(craft_model.read())
    with open(os.path.join(model_path, "english_g2.pth"), "wb") as f:
        f.write(lang_model.read())
    st.success("✅ Model files saved. You can now use the OCR below.")

# Only initialize reader if models are in place
reader = None
if os.path.exists(os.path.join(model_path, "craft_mlt_25k.pth")) and os.path.exists(os.path.join(model_path, "english_g2.pth")):
    reader = easyocr.Reader(['en'], gpu=False, model_storage_directory=model_path, download_enabled=False)

openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else ""

def invert_image_if_needed(img):
    grayscale = img.convert("L")
    pixels = list(grayscale.getdata())
    avg_brightness = sum(pixels) / len(pixels)
    return ImageOps.invert(img) if avg_brightness < 127 else img

def extract_text(file):
    text = ""
    if file.type == "application/pdf":
        doc = fitz.open(stream=file.read(), filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            img = invert_image_if_needed(img)
            np_img = np.array(img)
            results = reader.readtext(np_img, detail=0, paragraph=True)
            text += "\n".join(results) + "\n"
    else:
        img = Image.open(file)
        img = invert_image_if_needed(img)
        np_img = np.array(img)
        results = reader.readtext(np_img, detail=0, paragraph=True)
        text = "\n".join(results)
    return text

def extract_fields_with_gpt(text):
    fallback = {k: "" for k in ["Document Type", "Grantor", "Grantee", "Date of Instrument", "File Date", "Legal Description", "Clauses"]}
    if not openai.api_key:
        return fallback

    prompt = f"""Extract the following fields from the legal text below. Return as JSON:
Document Type, Grantor(s), Grantee(s), Date of Instrument, File Date, Legal Description, and any Title Clauses (e.g. reservations).
Text:
{text}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw_content = response.choices[0].message.content.strip()
        try:
            return json.loads(raw_content)
        except json.JSONDecodeError:
            st.warning("⚠️ GPT returned invalid JSON. Showing raw output below.")
            st.code(raw_content)
            return fallback
    except Exception as e:
        st.error(f"❌ GPT request failed: {e}")
        return fallback

# OCR Workflow
st.header("📤 Upload Documents")
uploaded_files = st.file_uploader("Upload PDFs or images", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files and reader:
    data = []
    for file in sorted(uploaded_files, key=lambda x: x.name.lower()):
        st.subheader(f"📄 {file.name}")
        ocr_text = extract_text(file)
        st.text_area("Extracted OCR Text", ocr_text, height=200)
        fields = extract_fields_with_gpt(ocr_text)
        data.append(fields)
        for k, v in fields.items():
            st.text_input(k, value=v if isinstance(v, str) else ", ".join(v) if isinstance(v, list) else str(v), key=f"{file.name}_{k}")

    if data:
        df = pd.DataFrame(data)
        xlsx_path = "/tmp/quantumdocs_output.xlsx"
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
            for col in writer.sheets['Sheet1'].columns:
                max_length = max(df[col.name].astype(str).map(len).max(), len(col.name))
                writer.sheets['Sheet1'].column_dimensions[col.name].width = max_length + 2
        st.success("✅ Excel file ready.")
        st.download_button("Download Excel", open(xlsx_path, "rb"), "quantumdocs_output.xlsx")
elif uploaded_files:
    st.warning("⚠️ Please upload both model files above first.")