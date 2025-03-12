from schema import ResumeData, HRFormData, Justification
from mongodb import get_collection
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.schema.runnable import RunnablePassthrough

# Function to Generate LLM Justification prompt
def generate_llm_justification(resume: ResumeData, hr_input: HRFormData):
    parser = PydanticOutputParser(pydantic_object=Justification)
    format_instructions = parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert HR assistant. Justify why a candidate is a good fit based on job criteria."),
        ("human", 
            "HR is hiring for {job_title}. They need someone with skills: {required_skills}, "
            "at least {min_experience} years of experience. Additional criteria: {additional_criteria}.\n\n"
            "Candidate Resume:\n"
            "- Name: {name}\n"
            "- Skills: {skills}\n"
            "- Experience: {experience}\n"
            "- Education: {education}\n"
            "- Certifications: {certifications}\n"
            "Be Honest and Provide structured justification why this candidate is a good fit or not with these fields:\n"
            "{format_instructions}"
        )
    ])

    formatted_prompt = prompt.format(
        job_title=hr_input.job_title,
        required_skills=", ".join(hr_input.required_skills),
        min_experience=hr_input.min_experience,
        additional_criteria=hr_input.additional_criteria,
        name=resume.name,
        skills=", ".join(resume.skills),
        experience=resume.experience,
        education=resume.education,
        certifications=resume.certifications,
        format_instructions=format_instructions
    )

    return formatted_prompt



# Fetch and Rank Candidates
def find_best_candidates(hr_input: HRFormData, llm):
    parser = PydanticOutputParser(pydantic_object=Justification)
    collection = get_collection()
    resumes = list(collection.find())  # Load resumes from MongoDB
    candidates = []

    for resume_data in resumes:
        resume = ResumeData(**resume_data)
        prompt = generate_llm_justification(resume, hr_input)
        chain = RunnablePassthrough() | llm | parser  
        justification = chain.invoke(prompt)
        candidates.append({"resume": resume, "justification": justification})
        print(f"📄 Justification Done for {resume.name}")

    # Sort candidates (future: use similarity ranking)
    candidates = sorted(candidates, key=lambda x: len(x["resume"].skills), reverse=True)

    # Select top N candidates
    return candidates[: hr_input.num_candidates], candidates[hr_input.num_candidates : hr_input.num_candidates + 2]
