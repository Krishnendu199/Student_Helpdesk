from crewai import Crew, Agent, Task
from Models.llm import get_ollama_model
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the Ollama3 LLM
llm = get_ollama_model()

def create_agent(name, role, goal):
    return Agent(
        role=role,
        goal=goal,
        backstory=f"{name} is responsible for {goal.lower()}",
        llm=llm,
        verbose=False
    )

# Define all agents
shortlisting_agent = create_agent(
    name="Shortlisting Agent",
    role="Admission Eligibility Verifier",
    goal="Evaluate the student's eligibility for admission based on academic performance and criteria."
)

document_checker_agent = create_agent(
    name="Document Checker Agent",
    role="Document Validator",
    goal="Verify if the submitted documents are complete and valid for the admission process."
)

student_counsellor_agent = create_agent(
    name="Student Counsellor",
    role="Admission Guidance Expert",
    goal="Guide students about the admission process, course offerings, and counseling."
)

student_loan_agent = create_agent(
    name="Student Loan Agent",
    role="Student Loan Advisor",
    goal="Assist students in understanding and applying for student loans."
)

def create_task(context, agent, expected_output):
    return Task(
        description=context,
        agent=agent,
        expected_output=expected_output
    )

def extract_student_info(data):
    return {
        "10th Marks": float(data.get("marks_10th", 0)),
        "12th Marks": float(data.get("marks_12th", 0))
    }

def extract_submitted_docs(data):
    return data.get("documents_submitted", []) or []

class AdmissionOfficer:
    def __init__(self):
        self.agents = {
            "shortlisting": shortlisting_agent,
            "document": document_checker_agent,
            "counsellor": student_counsellor_agent,
            "loan": student_loan_agent
        }
        self.chat_history = []

    def classify_intent(self, query):
        prompt = f"""
        Classify the following student query into one of the following categories:
        - eligibility
        - loan
        - document
        - counselling

        Only respond with the category name.

        Query: "{query}"
        """
        intent = llm.call(prompt).strip().lower()
        if intent not in ["eligibility", "loan", "document", "counselling"]:
            intent = "unknown"
        logger.info(f"[DEBUG] Detected intent: {intent}")
        return intent

    def validate_input(self, student_data):
        required_fields = ["name", "age", "course_applied", "marks_10th", "marks_12th"]
        for field in required_fields:
            if field not in student_data or student_data[field] in [None, ""]:
                return False, f"Missing or invalid field: {field}"
        return True, None

    def log_agent_output(self, agent_name, output):
        logger.info(f"[AGENT OUTPUT - {agent_name}]:\n{output}")
        self.chat_history.append((agent_name, output))

    def process_query(self, query, student_data):
        valid, error_msg = self.validate_input(student_data)
        if not valid:
            return f"⚠️ Error: {error_msg}. Please provide complete and correct student information."

        tasks = []
        student_name = student_data['name']

        context = f"""
        STUDENT PROFILE:
        Name: {student_name}
        Age: {student_data['age']}
        Course Applied: {student_data['course_applied']}
        Documents Submitted: {", ".join(student_data.get('documents_submitted', []))}
        Loan Requested: ₹{student_data.get('loan_requested', 0)}
        Income Certificate: {"Yes" if student_data.get('income_certificate') else "No"}
        Marks (10th): {student_data['marks_10th']}%
        Marks (12th): {student_data['marks_12th']}%

        STUDENT QUERY:
        {query}
        """

        intent = self.classify_intent(query)

        if intent == "eligibility":
            tasks.append(create_task(
                context,
                self.agents["shortlisting"],
                "Bullet-pointed evaluation of admission eligibility."
            ))
        
        elif intent == "loan":
            if not student_data.get("income_certificate"):
                keywords = ["apply", "submit", "get", "eligible", "loan"]
                if any(word in query.lower() for word in keywords):
                    return f"""
Dear {student_name},

Thank you for your interest in applying for a student loan. Please note that the Income Certificate is a mandatory requirement for processing any student loan application.

Unfortunately, we are unable to proceed until this document is submitted. Once you've uploaded the Income Certificate, feel free to apply again and our team will be happy to assist you.

Sincerely,  
Admissions & Finance Office
"""

            student = extract_student_info(student_data)
            submitted_docs = extract_submitted_docs(student_data)

            if student_data.get("income_certificate"):
                submitted_docs.append("Income Certificate")

            loan_criteria_ok = (
                student["10th Marks"] >= 50 and
                student["12th Marks"] >= 50
            )

            required_loan_docs = [
                "10th Marksheet",
                "12th Marksheet",
                "Aadhar Card",
                "Photo",
                "Income Certificate"
            ]

            def is_doc_submitted(doc_name, docs):
                norm = lambda s: s.lower().replace(" ", "").replace("marksheet", "")
                doc_name_norm = norm(doc_name)
                return any(doc_name_norm in norm(d) for d in docs)

            missing_docs = [doc for doc in required_loan_docs if not is_doc_submitted(doc, submitted_docs)]
            doc_check_ok = len(missing_docs) == 0

            loan_context = f"""
LOAN ELIGIBILITY CHECK:
To qualify for a student loan, the following are required:
- Minimum 50% marks in 10th and 12th
- Submission of: {", ".join(required_loan_docs)}

STUDENT PERFORMANCE:
- 10th Marks: {student['10th Marks']}% {"✅" if student['10th Marks'] >= 50 else "❌"}
- 12th Marks: {student['12th Marks']}% {"✅" if student['12th Marks'] >= 50 else "❌"}

DOCUMENT CHECK:
""" + "\n".join([
                f"- {'✅' if is_doc_submitted(doc, submitted_docs) else '❌'} {doc}: {'Submitted' if is_doc_submitted(doc, submitted_docs) else 'Missing'}"
                for doc in required_loan_docs
            ])

            if loan_criteria_ok and doc_check_ok:
                result = "🎉 Loan Eligibility Status: Eligible for Student Loan"
                closing = f"""

Dear {student_name},

Congratulations! Based on your academic performance and the documents you've submitted, you are eligible for a student loan. Our finance team will contact you shortly with the next steps in the process.

If you have any questions, feel free to reach out. We wish you all the best as you continue your journey with us.

Sincerely,  
Admissions & Finance Office"""
            else:
                result = "❌ Loan Eligibility Status: Not Eligible\n📌 Issues:\n"
                if not loan_criteria_ok:
                    if student["10th Marks"] < 50:
                        result += "- 10th marks are below 50%\n"
                    if student["12th Marks"] < 50:
                        result += "- 12th marks are below 50%\n"
                if not doc_check_ok:
                    result += "- Missing documents: " + ", ".join(missing_docs)
                closing = f"""

Dear {student_name},

Unfortunately, we are unable to approve your student loan application at this time due to the reasons mentioned above. Please review the criteria and submit any missing documents if applicable.

If you need support or clarification, our team is always here to assist you. We encourage you to reapply once the issues are resolved.

Sincerely,  
Admissions & Finance Office"""

            tasks.append(create_task(
                loan_context,
                self.agents["loan"],
                f"""Loan Eligibility Summary:
- ✅ or ❌ for marks and documents
- 📌 Mention all issues if not eligible
- End with final loan eligibility status

{result}{closing}"""
            ))

        elif intent == "document":
            def is_doc_submitted(doc_name, submitted_docs):
                norm = lambda s: s.lower().replace(" ", "").replace("marksheet", "")
                doc_name_norm = norm(doc_name)
                return any(doc_name_norm in norm(d) for d in submitted_docs)

            submitted_docs = extract_submitted_docs(student_data)

            context += f"""
DOCUMENT VALIDATION RULES:
The following documents are mandatory to approve admission:
- 10th Marksheet
- 12th Marksheet
- Aadhar Card
- Photo

DOCUMENT CHECK SUMMARY:
- {"✅" if is_doc_submitted("10th Marksheet", submitted_docs) else "❌"} 10th Marksheet: {"Submitted" if is_doc_submitted("10th Marksheet", submitted_docs) else "Missing"}
- {"✅" if is_doc_submitted("12th Marksheet", submitted_docs) else "❌"} 12th Marksheet: {"Submitted" if is_doc_submitted("12th Marksheet", submitted_docs) else "Missing"}
- {"✅" if is_doc_submitted("Aadhar Card", submitted_docs) else "❌"} Aadhar Card: {"Submitted" if is_doc_submitted("Aadhar Card", submitted_docs) else "Missing"}
- {"✅" if is_doc_submitted("Photo", submitted_docs) else "❌"} Photo: {"Submitted" if is_doc_submitted("Photo", submitted_docs) else "Missing"}
- {"⚠️ Transfer Certificate: Not Uploaded (not applicable)" if not is_doc_submitted("Transfer Certificate", submitted_docs) else "✅ Transfer Certificate: Submitted"}
"""

            all_required_present = all([
                is_doc_submitted("10th Marksheet", submitted_docs),
                is_doc_submitted("12th Marksheet", submitted_docs),
                is_doc_submitted("Aadhar Card", submitted_docs),
                is_doc_submitted("Photo", submitted_docs)
            ])

            final_status = (
                "✅ Admission Status: Approved 🎉" if all_required_present else
                "❌ Admission Status: Not Approved\n🔁 Action Required: Please upload missing documents to proceed"
            )

            if all_required_present:
                closing_note = f"""

Dear {student_name},

Thank you for submitting your documents. We have reviewed them and found everything in order. Your application is now ready for the next stage of admission processing.

Should anything further be required, we will reach out to you.

Sincerely,  
Admissions Committee"""
            else:
                closing_note = f"""

Dear {student_name},

Some required documents for your admission are still pending. Kindly refer to the checklist above and submit the missing items as soon as possible to avoid delays in your application.

For any help or guidance, please don’t hesitate to contact our support team.

Sincerely,  
Admissions Committee"""

            tasks.append(create_task(
                context,
                self.agents["document"],
                f"""Document Verification Summary:
- ✅ or ❌ for required documents
- ⚠️ for Transfer Certificate if not uploaded
- End with final admission status message

{final_status}{closing_note}"""
            ))

        elif intent == "counselling":
            tasks.append(create_task(
                context,
                self.agents["counsellor"],
                "Bullet-pointed advice and next steps for the student."
            ))

        else:
            return f"❓ Sorry, I couldn't understand your request. Could you rephrase it or choose a category like eligibility, loan, documents, or counselling?"

        crew = Crew(tasks=tasks)
        result = crew.kickoff()
        self.log_agent_output(intent, result)
        return result
