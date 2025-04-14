
import streamlit as st
from PIL import Image
import easyocr
import fitz  # PyMuPDF
import spacy
import io
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="QuantumDocs - EasyOCR Edition", layout="wide")
st.title("QuantumDocs")
st.subheader("Streamlit Cloud Compatible Version (EasyOCR Only)")

@st.cache_resource
def load_models():
    return easyocr.Reader(['en'], gpu=False), spacy.load("en_core_web_sm")

reader, nlp = load_models()

st.markdown("### Upload a scanned document (PDF, JPEG, PNG, or TIFF):")
uploaded_file = st.file_uploader("Choose a file", type=["png", "jpg", "jpeg", "tif", "tiff", "pdf"])

def extract_text_from_pdf(upload):
    text_output = ""
    doc = fitz.open(stream=upload.read(), filetype="pdf")
    for page in doc:
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes()))
        result = reader.readtext(np.array(img), detail=0)
        text_output += "\n".join(result) + "\n"
    return text_output

def extract_entities(text):
    doc = nlp(text)
    return {
        "People/Orgs": list(set(ent.text for ent in doc.ents if ent.label_ in ["PERSON", "ORG"])),
        "Dates": list(set(ent.text for ent in doc.ents if ent.label_ == "DATE")),
        "GPEs": list(set(ent.text for ent in doc.ents if ent.label_ == "GPE"))
    }

def classify_document_title(text, filename=None):
    text = text.lower()
    filename = filename.lower() if filename else ""
    if 'division order' in text:
        return 'Division Order'
    if 'ratification' in text:
        return 'Ratification'
    if 'assignment' in text:
        return 'Assignment'
    if 'oil and gas lease' in text or 'lease agreement' in text:
        return 'Oil & Gas Lease'
    if 'unit agreement' in text:
        return 'Unit Agreement'
    if 'plat map' in text or 'surveyed by' in text:
        return 'Wellsite Map / Survey'
    if 'affidavit' in text:
        return 'Affidavit'
    if 'memorandum of lease' in text:
        return 'Memorandum of Lease'
    if 'easement' in text:
        return 'Easement Agreement'
    if 'plat' in filename or 'survey' in filename:
        return 'Wellsite Map / Survey'
    if 'lease' in filename:
        return 'Oil & Gas Lease'
    return 'Uncategorized'

def extract_legal_description(text):
    match = re.findall(r"(?:Situated|Being|Containing|Described).*?(?:\n|\.){2,}", text, re.IGNORECASE | re.DOTALL)
    return match[0].strip() if match else ""

def extract_clauses_by_triggers(text):
    clause_triggers = [
        "reserving", "reserve", "hereby reserve", "subject to", "less and except",
        "excepting", "except", "save and except", "shall be retained", "shall not convey",
        "does not include", "excluding", "retaining", "there is hereby reserved",
        "grantor does not convey", "excluding all oil, gas and other minerals",
        "less and except all oil, gas, and other minerals", "reserving and excepting"
    ]
    text_lower = text.lower()
    sentences = re.split(r'(?<=[.\n])', text)
    matched_sentences = []

    for sentence in sentences:
        for trigger in clause_triggers:
            if trigger in sentence.lower():
                matched_sentences.append(sentence.strip())
                break

    return "\n---\n".join(matched_sentences)

if uploaded_file:
    file_type = uploaded_file.type
    raw_text = ""

    if "pdf" in file_type:
        raw_text = extract_text_from_pdf(uploaded_file)
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Document", use_column_width=True)
        raw_text = "\n".join(reader.readtext(np.array(image), detail=0))

    entities = extract_entities(raw_text)
    classification = classify_document_title(raw_text, uploaded_file.name)
    legal_desc = extract_legal_description(raw_text)
    clause_text = extract_clauses_by_triggers(raw_text)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Full OCR Text")
        st.text_area("Extracted Text", raw_text, height=500)

    with col2:
        st.markdown("### Extracted Fields (Structured View)")
        st.text_input("Document Title", classification)
        st.text_input("Grantor(s)", "")
        st.text_input("Grantee(s)", "")
        st.text_input("Date of Instrument", ", ".join(entities["Dates"][:1]))
        st.text_input("File Date of Document", ", ".join(entities["Dates"][1:2]))
        st.text_area("Legal Description", legal_desc, height=120)
        st.text_area("Clauses / Reservations", clause_text, height=180)

    st.markdown("### Export Structured Data")
    flat_entities = [(k, v) for k, vs in entities.items() for v in vs]
    flat_entities.append(("Classification", classification))
    df = pd.DataFrame(flat_entities, columns=["Entity Type", "Value"])
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download as CSV", csv, "quantumdocs_output.csv", "text/csv")
else:
    st.info("Upload a document to begin (PDF, JPEG, PNG, TIFF).")
