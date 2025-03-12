import pymongo
from pymongo import MongoClient
from schema import ResumeData

# MongoDB connection
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "resumes"
COLLECTION_NAME = "resumes"


# Connect to MongoDB
def connect_to_mongodb():
    try:
        client = MongoClient(MONGO_URI)
        print("✅ Connected to MongoDB!")
        return client
    except Exception as e:
        print("❌ Failed to connect to MongoDB:", e)
        return None


# Get the database
def get_database():
    client = connect_to_mongodb()
    if client:
        db = client[DB_NAME]
        print("✅ Database found!")
        return db
    else:
        return None


# Get the collection
def get_collection():
    db = get_database()
    if db is not None:  # ✅ Corrected check
        collection = db[COLLECTION_NAME]  # MongoDB creates it automatically on first insert
        print(f"✅ Collection '{COLLECTION_NAME}' ready!")
        return collection
    return None


def insert_resume_into_mongodb(resume_data: ResumeData):
    collection = get_collection()

    # Extract first name and education for duplicate check
    first_name = resume_data.name.first_name
    last_name = resume_data.name.last_name
    education_entries = resume_data.education

    if not education_entries:
        print(f"⚠️ No education details found for {first_name}, skipping duplicate check.")
        return  # Avoid storing incomplete data

    # Convert education list to a set of (degree, university) tuples for uniqueness check
    education_set = {(edu.degree, edu.university) for edu in education_entries}

    # Check if a resume with the same first name & education exists
    existing_resume = collection.find_one({
        "name.first_name": first_name,
        "name.last_name": last_name,
        "education": {"$elemMatch": {"degree": {"$in": [edu[0] for edu in education_set]},
                                     "university": {"$in": [edu[1] for edu in education_set]}}}
    })

    if existing_resume:
        print(f"🔄 Duplicate resume detected: {first_name}, skipping insertion.")
    else:
        collection.insert_one(resume_data.model_dump())
        print(f"✅ Resume added: {first_name}")
