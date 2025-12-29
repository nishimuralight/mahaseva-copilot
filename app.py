# MahaSeva Copilot v_FINAL_DEPLOYED: For deploying to Streamlit Cloud.
# This version has NO hardcoded paths and uses the hardened prompts to fix the AI hallucination bug.
# This is the definitive, correct code for deployment.

import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
import random
from urllib.parse import quote_plus
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import os

# --- OCR and PDF Engine Configuration (FOR DEPLOYMENT) ---
# All hardcoded Windows paths are REMOVED. The server will find the programs automatically.


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

# --- BILINGUAL, HARDENED PROMPTS ---

AUTO_EXTRACT_PROMPT_MR = """
You are a precise and factual AI assistant. Your output must be in Marathi.
Your single most important rule is to use **ONLY** the information from the GR Text provided below.

**CRITICAL RULES:**
1.  **DO NOT** invent information.
2.  **DO NOT** use any external knowledge.
3.  **DO NOT** make assumptions. If the GR is about a scheme for women, you must not mention farmers or any other group. Your answer must be 100% based on the text.

Based *only* on the GR Text, perform these tasks and format the output *exactly* as specified below.

### पात्रता निकष (Eligibility Criteria)
- [List all eligibility points here as a bulleted list in Marathi.]
- [If no information is found, you MUST write "माहिती उपलब्ध नाही"]

---

### अपात्रता निकष (Ineligibility Criteria)
- [List all ineligibility points here as a bulleted list in Marathi.]
- [If no information is found, you MUST write "माहिती उपलब्ध नाही"]

---

### आवश्यक कागदपत्रे (Required Documents)
- [List all required documents here as a bulleted list in Marathi.]
- [If no information is found, you MUST write "माहिती उपलब्ध नाही"]

GR Text:
---
{input_text}
---
"""

AUTO_EXTRACT_PROMPT_EN = """
You are a precise and factual AI assistant. Your output must be in English.
Your single most important rule is to use **ONLY** the information from the GR Text provided below.

**CRITICAL RULES:**
1.  **DO NOT** invent information.
2.  **DO NOT** use any external knowledge.
3.  **DO NOT** make assumptions. If the GR is about a scheme for women, you must not mention farmers or any other group. Your answer must be 100% based on the text.

Based *only* on the GR Text, perform these tasks and format the output *exactly* as specified below.

### Eligibility Criteria (पात्रता निकष)
- [List all eligibility points here as a bulleted list in English.]
- [If no information is found, you MUST write "Information not available"]

---

### Ineligibility Criteria (अपात्रता निकष)
- [List all ineligeligibility points here as a bulleted list in English.]
- [If no information is found, you MUST write "Information not available"]

---

### Required Documents (आवश्यक कागदपत्रे)
- [List all required documents here as a bulleted list in English.]
- [If no information is found, you MUST write "Information not available"]

GR Text:
---
{input_text}
---
"""

WHATSAPP_SUMMARY_PROMPT_EN = """
You are "MahaSeva Copilot," an AI assistant. Your task is to convert the following structured information into a simple, viral, and easy-to-read WhatsApp message in English.
Your summary must be based **ONLY** on the information provided below.

- Start with a catchy header with emojis (e.g., 📢 *Important Government Scheme Alert!*).
- Summarize the key points for Eligibility (✅ Eligibility), and Documents (📄 Documents).
- Use simple words, a bulleted list (using ● or ▪), and relevant emojis.
- End with a call to action to share the message (e.g., *Please share this information with everyone!* 🙏).

Structured Information:
---
{input_text}
---
"""

WHATSAPP_SUMMARY_PROMPT_MR = """
You are "MahaSeva Copilot," an AI assistant. Your task is to convert the following structured information into a simple, viral, and easy-to-read WhatsApp message in Marathi.
Your summary must be based **ONLY** on the information provided below.

- Start with a catchy header with emojis (e.g., 📢 *योजनेची महत्त्वाची माहिती!*).
- Summarize the key points for Eligibility (✅ पात्रता), and Documents (📄 कागदपत्रे).
- Use simple words, a bulleted list (using ● or ▪), and relevant emojis.
- End with a call to action to share the message (e.g., *ही माहिती सर्वांपर्यंत पोहोचवा!* 🙏).

Structured Information:
---
{input_text}
---
"""

PROMPT_TEMPLATES = {
    "en": {
        "AUTO_EXTRACT": AUTO_EXTRACT_PROMPT_EN,
        "WHATSAPP_SUMMARY": WHATSAPP_SUMMARY_PROMPT_EN
    },
    "mr": {
        "AUTO_EXTRACT": AUTO_EXTRACT_PROMPT_MR,
        "WHATSAPP_SUMMARY": WHATSAPP_SUMMARY_PROMPT_MR
    }
}


# --- Core AI and Helper Functions ---

def get_gemini_response(final_prompt):
    try:
        model = genai.GenerativeModel('models/gemini-flash-latest')
        response = model.generate_content(final_prompt)
        return response.text if response.text and response.text.strip() else None
    except Exception as e:
        st.error(f"An error occurred with the Gemini API: {e}")
        return None

def extract_text_from_pdf_robust(uploaded_file, T):
    def ocr_with_spinner(file_bytes):
        with st.spinner(T["processing_ocr"]):
            # The poppler_path argument is REMOVED for deployment
            images = convert_from_bytes(file_bytes)
            full_text = ""
            for img in images:
                # The config argument is REMOVED for deployment
                full_text += pytesseract.image_to_string(img, lang='mar+eng') + "\n"
        return full_text

    try:
        reader = pdf.PdfReader(uploaded_file)
        text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
        if text and len(text.strip()) > 100:
            return text
    except Exception:
        pass

    try:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        full_text = ocr_with_spinner(file_bytes)
        return full_text if full_text and full_text.strip() else None
    except Exception as e:
        st.error(f"PDF PROCESSING ERROR: {e}. Please ensure Tesseract and Poppler are correctly placed and paths are correct.")
        return None

# --- UI RENDER ---

if 'lang' not in st.session_state:
    st.session_state.lang = "mr"

# This simple logic is restored to prevent the blank screen bug.
T = LANGUAGES[st.session_state.lang]

# This is your original, simple UI.
st.title(T["title"])
st.markdown(T["subtitle"])

with st.sidebar:
    st.header(T["sidebar_header"])
    selected_lang_display = st.radio(
        T["lang_toggle"], ["मराठी (Marathi)", "English"],
        index=0 if st.session_state.lang == "mr" else 1, key="language_toggle"
    )
    st.session_state.lang = "mr" if "मराठी" in selected_lang_display else "en"
    # We need to update T if the language changes
    T = LANGUAGES[st.session_state.lang]
    
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
                auto_extract_prompt_template = PROMPT_TEMPLATES[st.session_state.lang]["AUTO_EXTRACT"]
                full_extract_prompt = auto_extract_prompt_template.format(input_text=pdf_text)
                
                extracted_data = get_gemini_response(full_extract_prompt)
                st.session_state.extracted_data = extracted_data
                
                if extracted_data:
                    whatsapp_prompt_template = PROMPT_TEMPLATES[st.session_state.lang]["WHATSAPP_SUMMARY"]
                    full_whatsapp_prompt = whatsapp_prompt_template.format(input_text=extracted_data)
                    
                    whatsapp_message = get_gemini_response(full_whatsapp_prompt)
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
                    T["whatsapp_copy_label"], st.session_state.whatsapp_message, height=400
                )
                st.success(T["whatsapp_success"], icon="✅")
            else:
                st.error(T["error_gemini"])
    elif st.session_state.get('file_identifier') and not st.session_state.get('extracted_data'):
        st.error("Could not automatically extract information. The GR format might be unusual or the text unreadable.")