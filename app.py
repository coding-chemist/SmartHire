import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain.output_parsers import PydanticOutputParser
from mongodb import insert_resume_into_mongodb
from schema import ResumeData, HRFormData
from utils import find_best_candidates
from dotenv import load_dotenv  

load_dotenv()

# Load the GROQ API Key from env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Ensure the "resumes" folder exists
RESUME_DIR = "./resumes"
os.makedirs(RESUME_DIR, exist_ok=True)

# Load LLMs
llm_groq = ChatGroq(groq_api_key=GROQ_API_KEY,
                    model="mistral-saba-24b")

st.set_page_config(page_title="SmartHire", page_icon="🤖", layout="wide")
st.title("AI Resume Screening System")


# Upload Resumes
uploaded_files = st.file_uploader("Upload Resumes (PDF/DOCX)", type=["pdf", "docx"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        save_path = os.path.join(RESUME_DIR, uploaded_file.name)
        
        # Save the file to the ./resumes directory
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write(f"✅ {uploaded_file.name} saved successfully!")

st.divider()

# HR Form (Only after upload)
if os.listdir(RESUME_DIR):  
    st.header("📝 HR Screening Form")

    with st.expander("Form", expanded=True):
        with st.form(key="hr_form"):
            job_title = st.text_input("Job Title")
            required_skills = st.text_area("Required Skills (comma-separated)")
            min_experience = st.number_input("Minimum Years of Experience", min_value=0, step=1)
            num_candidates = st.number_input("Number of Candidates to Select", min_value=1, step=1)
            additional_criteria = st.text_area("Additional Selection Criteria")

            # Form submission button
            submit_form = st.form_submit_button("🔍 Process & Match Resumes")

    # Submit - Store HR Input as Pydantic Model
    if submit_form:
        hr_input = HRFormData(
            job_title=job_title,
            required_skills=[skill.strip() for skill in required_skills.split(",") if skill.strip()],
            min_experience=int(min_experience),
            num_candidates=int(num_candidates),
            additional_criteria=additional_criteria
        )

        st.success("✅ HR Form Submitted Successfully!")

        with st.spinner("Processing resumes..."):
            # Load PDF Resumes
            pdf_loader = PyPDFDirectoryLoader(RESUME_DIR)
            pdf_documents = pdf_loader.load()

            # Load Word Doc Resumes
            doc_files = [f for f in os.listdir(RESUME_DIR) if f.endswith(".docx")]
            doc_documents = []
            for doc_file in doc_files:
                loader = Docx2txtLoader(os.path.join(RESUME_DIR, doc_file))
                doc_documents.extend(loader.load())

            # Combine all documents
            all_documents = pdf_documents + doc_documents  

            # Define the vector store
            parser = PydanticOutputParser(pydantic_object=ResumeData)

            # Define prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Extract structured resume data from the given document."),
                ("human", "{text}\n{format_instructions}")
            ]).partial(format_instructions=parser.get_format_instructions())


            # Define the chain
            chain = prompt | llm_groq | parser

            if all_documents:
                for doc in all_documents:
                    try:
                        extracted_data = chain.invoke({"text": doc.page_content})
                        insert_resume_into_mongodb(extracted_data)
                    except Exception as e:
                        st.write(f"❌ Error processing resume: {e}")

            best_candidates, next_matches = find_best_candidates(hr_input, llm_groq)

            if best_candidates:
                st.success(f"✅ Found {len(best_candidates)} best-matched candidates!")

                for idx, candidate in enumerate(best_candidates, start=1):
                    resume = candidate["resume"]
                    justification = candidate["justification"]

                    st.subheader(f"🏅 Candidate {idx}: {resume.name.first_name} {resume.name.last_name}")

                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("### Candidate Details")

                        # Convert Education List to Readable Text
                        education_text = "\n".join([f"- {edu.degree}, {edu.university} ({edu.year})" for edu in resume.education])
                        st.write(f"🎓 **Education:**\n{education_text}")

                        # Convert Experience List to Readable Text
                        experience_text = "\n".join([f"- {exp.title} at {exp.company} ({exp.year})" for exp in resume.experience])
                        st.write(f"💼 **Experience:**\n{experience_text}")

                        # Skills
                        st.write(f"🔧 **Skills:** {', '.join(resume.skills)}")

                        # Certifications
                        certifications_text = ", ".join([cert.name for cert in resume.certifications])
                        st.write(f"🏅 **Certifications:** {certifications_text if certifications_text else 'N/A'}")

                    with col2:
                        st.write("### LLM Justification")
                        st.write(f"📚 **Education Match:** {justification.edu_match}")
                        st.write(f"📈 **Experience Match:** {justification.exp_match}")
                        st.write(f"🔍 **Skill Match:** {justification.skill_match}")
                        st.write(f"🤝 **Team Player:** {justification.team_player}")
                        st.write(f"🎯 **Role Fit:** {justification.role_match}")
                        st.write(f"🧩 **SWOT Analysis:** {justification.swot_analysis}")
                        st.write(f"✅ **Final Justification:** {justification.final_justification}")

                # Expander for next best candidates
                if next_matches:
                    with st.expander("👀 See Next Possible Matches"):
                        for idx, candidate in enumerate(next_matches, start=len(best_candidates) + 1):
                            resume = candidate["resume"]
                            justification = candidate["justification"]

                            st.subheader(f"Candidate {idx}: {resume.name.first_name} {resume.name.last_name}")

                            col1, col2 = st.columns(2)

                            with col1:
                                st.write("### Candidate Details")

                                # Convert Education List to Readable Text
                                education_text = "\n".join([f"- {edu.degree}, {edu.university} ({edu.year})" for edu in resume.education])
                                st.write(f"🎓 **Education:**\n{education_text}")

                                # Convert Experience List to Readable Text
                                experience_text = "\n".join([f"- {exp.title} at {exp.company} ({exp.year})" for exp in resume.experience])
                                st.write(f"💼 **Experience:**\n{experience_text}")

                                # Skills
                                st.write(f"🔧 **Skills:** {', '.join(resume.skills)}")

                                # Certifications
                                certifications_text = ", ".join([cert.name for cert in resume.certifications])
                                st.write(f"🏅 **Certifications:** {certifications_text if certifications_text else 'N/A'}")

                            with col2:
                                st.write("### LLM Justification")
                                st.write(f"📚 **Education Match:** {justification.edu_match}")
                                st.write(f"📈 **Experience Match:** {justification.exp_match}")
                                st.write(f"🔍 **Skill Match:** {justification.skill_match}")
                                st.write(f"🤝 **Team Player:** {justification.team_player}")
                                st.write(f"🎯 **Role Fit:** {justification.role_match}")
                                st.write(f"🧩 **SWOT Analysis:** {justification.swot_analysis}")
                                st.write(f"✅ **Final Justification:** {justification.final_justification}")
                else:
                    st.warning("⚠️ No suitable candidates found based on the criteria.")
