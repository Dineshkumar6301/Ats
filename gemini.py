import streamlit as st
import os
import PyPDF2 as pdf
import docx2txt
import pandas as pd
import re

# Function to extract text from PDF files
def input_pdf_text(file_path):
    try:
        with open(file_path, "rb") as f:
            reader = pdf.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return ""

# Function to extract text from DOCX files
def input_docx_text(file_path):
    try:
        text = docx2txt.process(file_path)
        return text
    except Exception as e:
        st.error(f"Error reading DOCX file: {e}")
        return ""

# Function to extract details from resume text
def extract_details_from_text(text):
    details = {
        "Name": "Null",
        "Phone No": "Null",
        "Email ID": "Null",
        "Job Title": "Null",
        "Current Company": "Null",
        "Skills": "Null",
        "Location": "Null"
    }

    # Convert text to lowercase for easier pattern matching
    text = text.lower()

    # Define regex patterns for each field
    name_pattern = r"(name[:\s]*([A-Za-z\s]+))"
    phone_pattern = r"((?:\+?\d{1,3})?[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4})"
    email_pattern = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
    job_title_pattern = r"(job\s*title[:\s]*([A-Za-z\s]+))"
    company_pattern = r"(current\s*company[:\s]*([A-Za-z\s]+))"
    skills_pattern = r"(skills[:\s]*([A-Za-z\s,]+))"
    location_pattern = r"(location[:\s]*([A-Za-z\s]+))"

    # Extract details using regex patterns
    name_match = re.search(name_pattern, text)
    phone_match = re.search(phone_pattern, text)
    email_match = re.search(email_pattern, text)
    job_title_match = re.search(job_title_pattern, text)
    company_match = re.search(company_pattern, text)
    skills_match = re.search(skills_pattern, text)
    location_match = re.search(location_pattern, text)

    # Populate the details dictionary
    if name_match:
        details["Name"] = name_match.group(2).title()
    if phone_match:
        details["Phone No"] = phone_match.group(1)
    if email_match:
        details["Email ID"] = email_match.group(1)
    if job_title_match:
        details["Job Title"] = job_title_match.group(2).title()
    if company_match:
        details["Current Company"] = company_match.group(2).title()
    if skills_match:
        details["Skills"] = [skill.strip().title() for skill in skills_match.group(2).split(',')]
    if location_match:
        details["Location"] = location_match.group(2).title()

    return details

# Streamlit app function
def app():
    st.title("Resume Details Extractor (Local Processing)")

    # Input for folder path
    folder_path = st.text_input("Enter the folder path containing resumes")

    # Submit button
    submit = st.button("Submit")

    # Data list to hold extracted details
    data = []

    if submit:
        if folder_path:
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                # Iterate through files in the folder
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)

                    if filename.endswith('.pdf') or filename.endswith('.docx'):
                        try:
                            # Extract text from file
                            if filename.endswith('.pdf'):
                                text = input_pdf_text(file_path)
                            elif filename.endswith('.docx'):
                                text = input_docx_text(file_path)

                            # Extract details from text
                            if text:
                                details = extract_details_from_text(text)
                                data.append(details)
                            else:
                                st.warning(f"No text extracted from {filename}")

                        except Exception as e:
                            st.error(f"Error processing file {filename}: {e}")

                # Create a DataFrame and save to CSV
                if data:
                    df = pd.DataFrame(data)
                    csv_file_path = os.path.join(folder_path, 'resumes_extracted_details.csv')
                    df.to_csv(csv_file_path, index=False)
                    st.success(f"Data successfully saved to {csv_file_path}")
                    st.write(df)  # Display the extracted data
                else:
                    st.warning("No valid data extracted from the resumes.")
            else:
                st.error("Invalid folder path. Please enter a valid folder path.")
        else:
            st.error("Please enter a folder path.")

# Run the Streamlit app
if __name__ == "__main__":
    app()
