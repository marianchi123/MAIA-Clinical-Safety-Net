import streamlit as st
from maia_final import Full_MAIA_System

# 1. Page Configuration
st.set_page_config(page_title="M.A.I.A. Clinical Assistant", page_icon="🩺", layout="wide")

# 2. Load M.A.I.A. Core
@st.cache_resource
def load_maia():
    system = Full_MAIA_System()
    # Зареждаме начална история за двама различни демо пациенти
    system.memory.add_patient_record(
        patient_id="PATIENT-007", 
        clinical_text="The patient develops a dry cough and rashes from ACE inhibitors."
    )
    system.memory.add_patient_record(
        patient_id="PATIENT-008", 
        clinical_text="No known allergies. History of mild hypertension."
    )
    return system

maia = load_maia()

# --- Логика за управление на сесията и изчистване на чата ---
if "current_patient" not in st.session_state:
    st.session_state.current_patient = "PATIENT-007"

def on_patient_change():
    # Изчиства екрана при смяна на пациента от менюто
    st.session_state.messages = []

# 3. UI Design
st.title("🩺 M.A.I.A. | Medical AI Assistant")
st.markdown("---")

# Sidebar for patient data
with st.sidebar:
    st.header("👤 Patient Selection")
    
    # Падащо меню за избор на пациент
    selected_patient = st.selectbox(
        "Select Patient ID:", 
        options=["PATIENT-007", "PATIENT-008", "PATIENT-009"],
        key="current_patient",
        on_change=on_patient_change 
    )
    
    st.info(f"**Active ID:** {selected_patient}")
    
    # Динамично показване на профила (Алергии + Състояния)
    if selected_patient == "PATIENT-007":
        st.warning("**Known Allergies:** ACE inhibitors")
        st.error("**Pre-existing Conditions:** Bronchial Asthma")
    elif selected_patient == "PATIENT-008":
        st.success("**Known Allergies:** None documented")
        st.warning("**Pre-existing Conditions:** Mild Hypertension")
    else:
        st.success("**Known Allergies:** None documented")
        st.success("**Pre-existing Conditions:** None documented")

    st.success("**System Status:** All modules online")
    
    st.markdown("---")
    st.markdown("""
    ### ℹ️ About M.A.I.A.
    **Medical Artificial Intelligence Assistant**
    * 🔒 100% Local & Privacy-First
    * 🛡️ Multi-layer Safety RAG
    * 🧠 Powered by Llama 3.1 & NIH DB
    """)

# 4. Chat History Management
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages on screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Doctor's Input Field
# Текстовото поле показва за кого точно пишем бележката
if prompt := st.chat_input(f"Enter clinical note for {selected_patient}..."):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner(f"⏳ M.A.I.A. is checking records for {selected_patient}..."):
            # Подаваме ДИНАМИЧНИЯ пациент към ядрото
            response = maia.run_consultation(patient_id=selected_patient, doctor_note=prompt)
            st.markdown(response)
            
    st.session_state.messages.append({"role": "assistant", "content": response})