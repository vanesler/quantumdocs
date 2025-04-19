
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

# ✅ Force path to Tesseract (for Render deployment)
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
st.write("Tesseract path:", pytesseract.pytesseract.tesseract_cmd)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-..."))

st.set_page_config(page_title="QuantumDocs: Sorted OCR", layout="wide")
st.title("🔷 QuantumDocs: Sorted OCR by Filename")

uploaded_files = st.file_uploader("📁 Upload documents (processed in filename order)", type=["pdf", "png", "jpg", "jpeg", "tif"], accept_multiple_files=True)

# Remaining functions unchanged for brevity...
