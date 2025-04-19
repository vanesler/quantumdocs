import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageOps
import io
import openai
import pandas as pd
import easyocr
import numpy as np

st.set_page_config(page_title="QuantumDocs Online", layout="wide")
st.title("🔷 QuantumDocs OCR with EasyOCR")

reader = easyocr.Reader(['en'], gpu=False)

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
    if not openai.api_key:
        return {k: "" for k in ["Document Type", "Grantor", "Grantee", "Date of Instrument", "File Date", "Legal Description", "Clauses"]}
    prompt = f"""Extract the following fields from the legal text below. Return as JSON:
    Document Type, Grantor(s), Grantee(s), Date of Instrument, File Date, Legal Description, and any Title Clauses (e.g. reservations).
    Text:
    {text}
    """.strip()
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Field extraction error: {e}")
        return {}

uploaded_files = st.file_uploader("Upload PDFs or images", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    data = []
    for file in sorted(uploaded_files, key=lambda x: x.name.lower()):
        st.header(f"📄 {file.name}")
        ocr_text = extract_text(file)
        st.text_area("Extracted OCR Text", ocr_text, height=200)
        fields = extract_fields_with_gpt(ocr_text)
        data.append(fields)
        for k, v in fields.items():
            st.text_input(k, value=v if isinstance(v, str) else ", ".join(v) if isinstance(v, list) else str(v), key=f"{file.name}_{k}")

    if data:
        df = pd.DataFrame(data)
        xlsx_path = "/mnt/data/quantumdocs_output.xlsx"
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
            for col in writer.sheets['Sheet1'].columns:
                max_length = max(df[col.name].astype(str).map(len).max(), len(col.name))
                writer.sheets['Sheet1'].column_dimensions[col.name].width = max_length + 2
        st.success("✅ Excel file ready.")
        st.download_button("Download Excel", open(xlsx_path, "rb"), "quantumdocs_output.xlsx")
else:
    st.info("Upload one or more PDF/image files to begin.")