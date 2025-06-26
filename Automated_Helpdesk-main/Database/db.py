import chromadb

# Connect to ChromaDB server
client = chromadb.HttpClient(host="localhost", port=8000)

# Get or create collection
def get_student_collection():
    return client.get_or_create_collection(name="students")

# Add or update student data
def add_student_data(data):
    collection = get_student_collection()
    student_id = data["name"].lower()

    # Step 1: Delete old record
    try:
        collection.delete(ids=[student_id])
        print(f"✅ Deleted old profile for: {student_id}")
    except Exception as e:
        print(f"⚠️ Couldn't delete existing record (maybe doesn't exist): {e}")

    # Step 2: Sanitize and convert all fields
    sanitized_data = {}
    for key, value in data.items():
        if isinstance(value, list):
            sanitized_data[key] = ", ".join(value)  # convert list to string
        elif isinstance(value, bool):
            sanitized_data[key] = str(value)  # convert bool to string
        elif isinstance(value, (int, float)):
            sanitized_data[key] = str(value)  # convert numbers to string
        else:
            sanitized_data[key] = value  # assume already string

    # Step 3: Log what is being saved
    print(f"✅ Saving updated profile for {student_id}:")
    for k, v in sanitized_data.items():
        print(f"   {k}: {v}")

    # Step 4: Save it
    collection.add(
        ids=[student_id],
        documents=["student_profile"],
        metadatas=[sanitized_data]
    )


# Retrieve student data by name
def get_student_by_name(name):
    collection = get_student_collection()
    student_id = name.lower()

    try:
        result = collection.get(ids=[student_id])
        if result and "metadatas" in result and result["metadatas"]:
            metadata = result["metadatas"][0]

            # Convert documents_submitted back to list
            if "documents_submitted" in metadata and isinstance(metadata["documents_submitted"], str):
                metadata["documents_submitted"] = [doc.strip() for doc in metadata["documents_submitted"].split(",")]

            # Convert numeric values back to their types
            for key in ["marks_10th", "marks_12th", "loan_requested"]:
                if key in metadata and isinstance(metadata[key], str):
                    try:
                        metadata[key] = float(metadata[key])
                    except:
                        metadata[key] = 0.0

            if "age" in metadata and isinstance(metadata["age"], str):
                try:
                    metadata["age"] = int(metadata["age"])
                except:
                    metadata["age"] = 0

            if "income_certificate" in metadata and isinstance(metadata["income_certificate"], str):
                metadata["income_certificate"] = metadata["income_certificate"].lower() == "true"

            return metadata

    except Exception as e:
        print("❌ Error in get_student_by_name():", e)

    return None

# Delete student profile
def delete_student_by_name(name):
    collection = get_student_collection()
    student_id = name.lower()

    try:
        collection.delete(ids=[student_id])
        print(f"✅ Deleted student profile for '{name}'")
    except Exception as e:
        print(f"❌ Failed to delete student '{name}': {e}")
