from pydantic import BaseModel, Field
from typing import List, Optional


# Name Model
class Name(BaseModel):
    first_name: str = Field(..., description="Candidate's first name")
    last_name: str = Field(..., description="Candidate's last name")


# Experience Model
class Experience(BaseModel):
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    year: str = Field(..., description="Year of employment")


# Education Model
class Education(BaseModel):
    degree: str = Field(..., description="Degree earned")
    university: str = Field(..., description="University name")
    year: Optional[str] = Field(None, description="Graduation year")
    gpa: Optional[float] = Field(None, description="GPA (if available)")


# Certifications Model
class Certification(BaseModel):
    name: str = Field(..., description="Certification name")
    provider: str = Field(..., description="Issuing organization")
    year: Optional[str] = Field(None, description="Year earned")


# ResumeData Model (Main Model)
class ResumeData(BaseModel):
    name: Name
    job_title: str = Field(..., description="Current job title")
    experience: List[Experience] = Field(..., description="Past companies and roles")
    skills: List[str] = Field(..., description="Technical & soft skills")
    education: List[Education] = Field(..., description="Degree & university details")
    certifications: List[Certification] = Field(..., description="Professional certifications")
    github: Optional[str] = Field(None, description="GitHub profile link")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile link")
    other_info: Optional[str] = Field(None, description="Any extra information")


# HR Input Model
class HRFormData(BaseModel):
    job_title: str = Field(..., description="Job title for the position")
    required_skills: list[str] = Field(..., description="Required skills (comma-separated)")
    min_experience: int = Field(..., description="Minimum years of experience required")
    num_candidates: int = Field(..., description="Number of candidates to select")
    additional_criteria: str = Field(None, description="Additional selection criteria")


# Justification Model
class Justification(BaseModel):
    edu_match: str = Field(..., description="Education match explanation")
    exp_match: str = Field(..., description="Experience match explanation")
    skill_match: str = Field(..., description="Skill match explanation")
    team_player: str = Field(..., description="Teamwork evaluation")
    role_match: str = Field(..., description="How well the candidate fits the role")
    swot_analysis: str = Field(..., description="Strengths, Weaknesses, Opportunities, Threats analysis")
    final_justification: str = Field(..., description="Final hiring recommendation")
