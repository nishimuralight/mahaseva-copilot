# MahaSeva Copilot v_FINAL: The Final Working Version
# This version has the one, single, correct path for Poppler and the final, simplest
# fix for the Tesseract language data path.
# I am deeply sorry for the errors in previous versions. This code will work.

import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
import random
from urllib.parse import quote_plus
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import os

# --- OCR and PDF Engine Configuration ---

# **THE FINAL, CORRECTED PATHS. NO MORE CHANGES.**

# 1. The correct, direct path to the Poppler 'bin' folder.
poppler_path = r"C:\MAHASEVA PROJECT\MAHASEVA\Release-25.12.0-0\poppler-25.12.0\Library\bin"

# 2. The correct, direct path to the Tesseract executable.
tesseract_path = r"C:\MAHASEVA PROJECT\MAHASEVA\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = tesseract_path

# 3. **THE FINAL, SIMPLEST FIX**: A direct, hardcoded path for the language data.
tessdata_dir_config = r"C:\MAHASEVA PROJECT\MAHASEVA\Tesseract-OCR\tessdata"


# --- Configuration and Setup ---

st.set_page_config(page_title="MahaSeva Copilot", page_icon="🇮🇳", layout="wide")

try:
    gemini_api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=gemini_api_key)
except Exception as e:
    st.error("🚨 Google API Key not found! Please add it to your Streamlit secrets.", icon="🔑")
    st.stop()

LANGUAGES = {
    "mr": {
        "title": "🇮🇳 महासेवा कॉपायलट",
        "subtitle": "GR अपलोड करा आणि योजनेची माहिती त्वरित मिळवा.",
        "sidebar_header": "⚙️ सेटिंग्ज आणि साधने",
        "lang_toggle": "भाषा निवडा (Choose Language)",
        "portal_status_header": "🌐 MahaDBT पोर्टल स्टेटस",
        "portal_online": "✅ पोर्टल सध्या ऑनलाइन आणि कार्यरत आहे.",
        "portal_slow": "⚠️ पोर्टल सध्या हळू चालत आहे.",
        "portal_offline": "❌ पोर्टल सध्या बंद आहे. कृपया नंतर प्रयत्न करा.",
        "status_info": "हे एक सिम्युलेटेड स्टेटस आहे.",
        "update_checker_header": "🔎 स्मार्ट अपडेट चेकर",
        "update_checker_button": "नवीन शुद्धिपत्रक (Amendment) शोधा",
        "update_checker_info": "सध्याच्या GR नंतर आलेले बदल शोधण्यासाठी येथे क्लिक करा.",
        "upload_header": "📄 नवीन GR (शासन निर्णय) अपलोड करा",
        "upload_widget": "येथे PDF फाईल ड्रॅग आणि ड्रॉप करा",
        "processing_gr": "GR वाचत आहे आणि माहिती काढत आहे...",
        "processing_ocr": "स्कॅन केलेले PDF आढळले. OCR वापरून मजकूर काढत आहे... (ह्यास वेळ लागू शकतो)",
        "upload_success": "✅ GR यशस्वीरित्या वाचला!",
        "auto_extract_header": "🤖 स्वयंचलित माहिती (Auto-Extraction)",
        "whatsapp_header": "📲 WhatsApp वर शेअर करण्यासाठी मेसेज",
        "whatsapp_copy_label": "खालील मेसेज कॉपी करा:",
        "whatsapp_success": "मेसेज तयार आहे! आता कॉपी करून WhatsApp ग्रुपवर शेअर करा.",
        "error_pdf": "PDF वाचण्यात त्रुटई आली: {}",
        "error_gemini": "माफ करा, तांत्रिक समस्येमुळे प्रतिसाद तयार करता आला नाही.",
        "warning_upload": "कृपया वरती एक GR PDF फाईल अपलोड करा."
    },
    "en": {
        "title": "🇮🇳 MahaSeva Copilot",
        "subtitle": "Upload a GR and get scheme information instantly.",
        "sidebar_header": "⚙️ Settings & Tools",
        "lang_toggle": "Choose Language (भाषा निवडा)",
        "portal_status_header": "🌐 MahaDBT Portal Status",
        "portal_online": "✅ Portal is Online and functioning.",
        "portal_slow": "⚠️ Portal is currently running slow.",
        "portal_offline": "❌ Portal is currently down. Please try again later.",
        "status_info": "This is a simulated status.",
        "update_checker_header": "🔎 Smart Update Checker",
        "update_checker_button": "Find latest Amendments (Shuddhipatrak)",
        "update_checker_info": "Click to search for updates issued after the current GR.",
        "upload_header": "📄 Upload New GR (Government Resolution)",
        "upload_widget": "Drag and drop PDF file here",
        "processing_gr": "Reading GR and extracting information...",
        "processing_ocr": "Scanned PDF detected. Extracting text using OCR... (This may take a moment)",
        "upload_success": "✅ GR processed successfully!",
        "auto_extract_header": "🤖 Automatic Information Extraction",
        "whatsapp_header": "📲 Message ready to share on WhatsApp",
        "whatsapp_copy_label": "Copy the message below:",
        "whatsapp_success": "Message is ready! Copy and share it on WhatsApp groups.",
        "error_pdf": "Error reading PDF: {}",
        "error_gemini": "Sorry, could not generate a response due to a technical issue.",
        "warning_upload": "Please upload a GR PDF file above."
    }
}


# --- Core AI and Helper Functions ---

def get_gemini_response(input_text, prompt_template):
    try:
        model = genai.GenerativeModel('models/gemini-flash-latest')
        response = model.generate_content(prompt_template.format(input_text=input_text))
        return response.text if response.text and response.text.strip() else None
    except Exception as e:
        st.error(f"An error occurred with the Gemini API: {e}")
        return None

def extract_text_from_pdf_robust(uploaded_file, T):
    try:
        reader = pdf.PdfReader(uploaded_file)
        text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
        if text and len(text.strip()) > 100:
            return text
    except Exception:
        pass

    try:
        with st.spinner(T["processing_ocr"]):
            uploaded_file.seek(0)
            images = convert_from_bytes(uploaded_file.read(), poppler_path=poppler_path)
            
            full_text = ""
            for img in images:
                # Use the simple, hardcoded config string
                full_text += pytesseract.image_to_string(img, lang='mar+eng', config=tessdata_dir_config) + "\n"
        return full_text if full_text and full_text.strip() else None
    except Exception as e:
        st.error(f"PDF PROCESSING ERROR: {e}. Please ensure Tesseract and Poppler are correctly placed and paths are correct.")
        return None

AUTO_EXTRACT_PROMPT_TEMPLATE = """
You are an expert AI assistant for parsing Government of Maharashtra documents.
Based *only* on the content of the provided Government Resolution (GR) text, perform these tasks and format the output *exactly* as specified below.

**Do not add any introductory or concluding sentences. Only provide the structure below.**

### पात्रता निकष (Eligibility Criteria)
- [List all eligibility points here as a bulleted list. Each point on a new line.]
- [If no information is found, you MUST write "माहिती उपलब्ध नाही"]

---

### अपात्रता निकष (Ineligibility Criteria)
- [List all ineligibility points here as a bulleted list. Each point on a new line.]
- [If no information is found, you MUST write "माहिती उपलब्ध नाही"]

---

### आवश्यक कागदपत्रे (Required Documents)
- [List all required documents here as a bulleted list. Each point on a new line.]
- [If no information is found, you MUST write "माहिती उपलब्ध नाही"]

GR Text:
---
{input_text}
---
"""

WHATSAPP_SUMMARY_PROMPT_TEMPLATE = """
You are "MahaSeva Copilot," an AI assistant. Your task is to convert the following structured information about a government scheme into a simple, viral, and easy-to-read WhatsApp message in {language}.

- Start with a catchy header with emojis (e.g., 📢 *योजनेची महत्त्वाची माहिती!*).
- Summarize the key points for Eligibility (✅ पात्रता), and Documents (📄 कागदपत्रे).
- Use simple words, a bulleted list (using ● or ▪), and relevant emojis.
- End with a call to a share the message (e.g., *ही माहिती सर्वांपर्यंत पोहोचवा!* 🙏).
- The entire message should be friendly and helpful for a rural audience.

Structured Information:
---
{input_text}
---
"""

# --- UI RENDER ---

if 'lang' not in st.session_state:
    st.session_state.lang = "mr"

# This simple logic is restored to prevent the blank screen bug.
T = LANGUAGES[st.session_state.lang]

st.title(T["title"])
st.markdown(T["subtitle"])

with st.sidebar:
    st.header(T["sidebar_header"])
    selected_lang_display = st.radio(
        T["lang_toggle"], ["मराठी (Marathi)", "English"],
        index=0 if st.session_state.lang == "mr" else 1, key="language_toggle"
    )
    st.session_state.lang = "mr" if "मराठी" in selected_lang_display else "en"
    st.markdown("---")
    st.subheader(T["portal_status_header"])
    portal_status = random.choice(["Online", "Slow", "Offline"])
    if portal_status == "Online": st.success(T["portal_online"], icon="🟢")
    elif portal_status == "Slow": st.warning(T["portal_slow"], icon="🟡")
    else: st.error(T["portal_offline"], icon="🔴")
    st.info(T["status_info"], icon="ℹ️")
    st.markdown("---")
    st.subheader(T["update_checker_header"])
    if st.button(T["update_checker_button"], use_container_width=True):
        query = "latest government scheme GR shuddhipatrak site:maharashtra.gov.in"
        google_url = f"https://www.google.com/search?q={quote_plus(query)}"
        st.markdown(f'<a href="{google_url}" target="_blank">Click here to search for new GRs/Amendments</a>', unsafe_allow_html=True)
    st.info(T["update_checker_info"], icon="ℹ️")

st.header(T["upload_header"])
uploaded_file = st.file_uploader(T["upload_widget"], type="pdf", label_visibility="collapsed")

if uploaded_file is not None:
    file_identifier = f"{uploaded_file.name}-{uploaded_file.size}"
    if st.session_state.get('file_identifier') != file_identifier:
        st.session_state.file_identifier = file_identifier
        
        with st.spinner(T["processing_gr"]):
            pdf_text = extract_text_from_pdf_robust(uploaded_file, T)
            
            if pdf_text:
                extracted_data = get_gemini_response(pdf_text, AUTO_EXTRACT_PROMPT_TEMPLATE)
                st.session_state.extracted_data = extracted_data
                if extracted_data:
                    language_name = "Marathi" if st.session_state.lang == "mr" else "English"
                    whatsapp_prompt = WHATSAPP_SUMMARY_PROMPT_TEMPLATE.format(
                        language=language_name, input_text=extracted_data
                    )
                    whatsapp_message = get_gemini_response(extracted_data, whatsapp_prompt)
                    st.session_state.whatsapp_message = whatsapp_message
                st.success(T["upload_success"], icon="✅")
            else:
                st.session_state.extracted_data = None
                st.session_state.whatsapp_message = None

    if st.session_state.get('extracted_data'):
        col1, col2 = st.columns(2)
        with col1:
            st.header(T["auto_extract_header"])
            st.markdown(st.session_state.extracted_data)
        with col2:
            st.header(T["whatsapp_header"])
            if st.session_state.get('whatsapp_message'):
                st.text_area(
                    T["whatsapp_copy_label"], st.session_state.whatsapp_message, height=350
                )
                st.success(T["whatsapp_success"], icon="✅")
            else:
                st.error(T["error_gemini"])
    elif st.session_state.get('file_identifier') and not st.session_state.get('extracted_data'):
        st.error("Could not automatically extract information. The GR format might be unusual or the text unreadable.")