import sys
import os
import streamlit as st

# Add root project directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Agents.agent import AdmissionOfficer
from Database.db import get_student_by_name, add_student_data, delete_student_by_name

# Page config
st.set_page_config(page_title="🎓 Admission Helpdesk Chatbot", page_icon="🎓", layout="centered")

# Styling
st.markdown("""
    <style>
    /* Chat Message Styling */
    .stChatMessage.user {
        background: linear-gradient(135deg, #DCF8C6, #c1e8b4);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 12px;
        font-size: 16px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
    }
    .stChatMessage.assistant {
        background: linear-gradient(135deg, #F1F0F0, #e2e2e2);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 12px;
        font-size: 16px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
    }

    /* Student Profile Card */
    .student-profile {
        background-color: #ffffff;
        padding: 20px;
        border-left: 6px solid #4CAF50;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        font-size: 15px;
    }

    /* General input field styling */
    input, select, textarea {
        border-radius: 6px !important;
    }

    /* Form section styling */
    section[data-testid="stForm"] {
        background-color: #fdfdfd;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e2e2e2;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    }

    /* Title and subtitle */
    h1, h2, h3 {
        color: #2e7d32;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Buttons */
    button {
        border-radius: 8px !important;
        padding: 10px 18px !important;
        font-weight: 600 !important;
        background-color: #4CAF50 !important;
        color: white !important;
    }

    button:hover {
        background-color: #45a049 !important;
    }

    /* Chat input alignment */
    .st-emotion-cache-1wmy9hl {
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 Admission Officer Chatbot")
st.markdown("Ask me anything about student admissions, documents, loans, and eligibility!")

# Input student name
student_name = st.text_input("👤 Enter your full name to load your profile:")

student_profile = None

if student_name:
    student_profile = get_student_by_name(student_name)

    if student_profile and isinstance(student_profile, dict):
        st.success(f"Student profile loaded for **{student_profile['name']}**")

        # Display profile
        st.markdown(f"""
        <div class="student-profile">
            <strong>📄 Name:</strong> {student_profile['name']}<br>
            <strong>🎓 Course Applied:</strong> {student_profile['course_applied']}<br>
            <strong>📊 10th Marks:</strong> {student_profile['marks_10th']}%<br>
            <strong>📊 12th Marks:</strong> {student_profile['marks_12th']}%<br>
            <strong>📁 Documents:</strong> {", ".join(student_profile['documents_submitted'])}<br>
            <strong>💰 Loan Requested:</strong> ₹{student_profile['loan_requested']}<br>
            <strong>📄 Income Certificate:</strong> {"Yes" if student_profile['income_certificate'] else "No"}
        </div>
        """, unsafe_allow_html=True)

        # Action buttons
        col1, col2 = st.columns(2)

        with col1:
            with st.expander("✏️ Edit Profile"):
                with st.form("edit_student_form"):
                    age = st.number_input("Age", value=int(student_profile["age"]), min_value=16, max_value=60, step=1)
                    course = st.text_input("Course Applied", value=student_profile["course_applied"])
                    marks_10 = st.number_input("10th Marks (%)", value=float(student_profile["marks_10th"]), min_value=0.0, max_value=100.0)
                    marks_12 = st.number_input("12th Marks (%)", value=float(student_profile["marks_12th"]), min_value=0.0, max_value=100.0)
                    docs = st.multiselect(
                        "Documents Submitted",
                        ["Marksheet 10th", "Marksheet 12th", "Aadhar Card", "Photo", "Transfer Certificate"],
                        default=student_profile["documents_submitted"]
                    )
                    loan_amt = st.number_input("Loan Amount Requested (₹)", value=float(student_profile["loan_requested"]), min_value=0.0)
                    income_cert = st.checkbox("Do you have an income certificate?", value=bool(student_profile["income_certificate"]))
                    submit_edit = st.form_submit_button("Save Changes")

                    if submit_edit:
                        updated_profile = {
                            "name": student_profile["name"],
                            "age": int(age),
                            "course_applied": course,
                            "marks_10th": float(marks_10),
                            "marks_12th": float(marks_12),
                            "documents_submitted": docs,
                            "loan_requested": float(loan_amt),
                            "income_certificate": income_cert
                        }
                        add_student_data(updated_profile)
                        st.success("✅ Profile updated successfully.")
                        st.rerun()

        with col2:
            if st.button("🗑️ Delete Profile"):
                delete_student_by_name(student_profile["name"])
                st.success("🗑️ Profile deleted. Please refresh.")
                st.stop()

    else:
        st.warning("No profile found. Please enter details to register:")
        with st.form("new_student_form"):
            name = student_name
            age = st.number_input("Age", min_value=16, max_value=60, step=1)
            course = st.text_input("Course Applied")
            marks_10 = st.number_input("10th Marks (%)", min_value=0.0, max_value=100.0)
            marks_12 = st.number_input("12th Marks (%)", min_value=0.0, max_value=100.0)
            docs = st.multiselect("Documents Submitted", ["Marksheet 10th", "Marksheet 12th", "Aadhar Card", "Photo", "Transfer Certificate"])
            loan_amt = st.number_input("Loan Amount Requested (₹)", min_value=0.0)
            income_cert = st.checkbox("Do you have an income certificate?")
            submit_btn = st.form_submit_button("Submit")

            if submit_btn:
                if not (course and docs and marks_10 and marks_12):
                    st.error("❌ Please fill all required fields.")
                else:
                    student_profile = {
                        "name": name,
                        "age": age,
                        "course_applied": course,
                        "marks_10th": marks_10,
                        "marks_12th": marks_12,
                        "documents_submitted": docs,
                        "loan_requested": loan_amt,
                        "income_certificate": income_cert
                    }
                    add_student_data(student_profile)
                    st.success("✅ Student profile created and stored in ChromaDB.")
                    st.rerun()

# Start chatbot if profile is available
if student_profile and isinstance(student_profile, dict):
    if "messages" not in st.session_state:
        st.session_state.messages = []

    officer = AdmissionOfficer()

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(f"🧑‍🎓 {msg['content']}" if msg["role"] == "user" else f"🎓 {msg['content']}")

    # New query
    query = st.chat_input("💬 Type your admission-related query here...")

    if query:
        st.chat_message("user").markdown(f"🧑‍🎓 {query}")
        st.session_state.messages.append({"role": "user", "content": query})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = officer.process_query(query, student_profile)
                    st.markdown(f"🎓 {response}")
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error("⚠️ Error processing query. Please try again.")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Sorry, something went wrong: {str(e)}"
                    })
