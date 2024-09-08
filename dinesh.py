import streamlit as st
import os
import PyPDF2 as pdf
import pandas as pd
import docx2txt
import re

# Function to extract text from PDF files
def input_pdf_text(uploaded_file):
    try:
        reader = pdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return ""

# Function to extract text from DOCX files
def input_docx_text(uploaded_file):
    try:
        text = docx2txt.process(uploaded_file)
        return text
    except Exception as e:
        st.error(f"Error reading DOCX file: {e}")
        return ""

# Function to extract details from text
def extract_details_from_text(text):
    details = {
        "Name": "",
        "Phone no": "",
        "Email id": "",
        "Job Title": "",
        "Current Company": "",
        "Skills": "",
        "Location": ""
    }

    # Normalize text for consistent processing
    text = text.lower().strip()

    # Define regex patterns for each field (improved regex patterns)
    name_pattern = r"(?i)(?:name|full\s*name)[\s:]*([\w\s]+)"
    phone_pattern = r"(?i)(?:phone\s*number|phone|telephone|mobile)[\s:]*([\d\s\-\(\)\+]+)"
    email_pattern = r"(?i)(?:email)[\s:]*([\w\.-]+@[\w\.-]+\.[a-z]+)"
    job_title_pattern = r"(?i)(?:job\s*title|position)[\s:]*([\w\s]+)"
    company_pattern = r"(?i)(?:current\s*company|employer)[\s:]*([\w\s]+)"
    skills_pattern = r"(?i)(?:skills)[\s:]*\[(.*?)\]|(?:skills)[\s:]*([\w\s,]+)"
    location_pattern = r"(?i)(?:location|address)[\s:]*([\w\s]+)"

    # Extract details using regex patterns
    name_match = re.search(name_pattern, text)
    phone_match = re.search(phone_pattern, text)
    email_match = re.search(email_pattern, text)
    job_title_match = re.search(job_title_pattern, text)
    company_match = re.search(company_pattern, text)
    skills_match = re.search(skills_pattern, text)
    location_match = re.search(location_pattern, text)

    # Fill details dictionary with extracted data
    if name_match:
        details["Name"] = name_match.group(1).strip().title()
    if phone_match:
        details["Phone no"] = phone_match.group(1).strip()
    if email_match:
        details["Email id"] = email_match.group(1).strip()
    if job_title_match:
        details["Job Title"] = job_title_match.group(1).strip().title()
    if company_match:
        details["Current Company"] = company_match.group(1).strip().title()
    if skills_match:
        # Support both comma-separated skills and skill lists in square brackets
        skills = skills_match.group(1) if skills_match.group(1) else skills_match.group(2)
        if skills:
            details["Skills"] = [skill.strip().title() for skill in skills.split(',')]
    if location_match:
        details["Location"] = location_match.group(1).strip().title()

    return details

# Streamlit app
st.title("Resume Details Extractor")

# Option 1: Allow folder input for batch processing
folder_path = st.text_input("Enter the folder path containing resumes")

# Option 2: File uploader for individual file upload
uploaded_file = st.file_uploader("Or upload a resume (PDF or DOCX)", type=["pdf", "docx"])

submit = st.button("Submit")

data = []  # Initialize data list outside the conditional blocks

if submit:
    if uploaded_file is not None:
        # Process individual uploaded file
        try:
            if uploaded_file.name.endswith('.pdf'):
                text = input_pdf_text(uploaded_file)
            elif uploaded_file.name.endswith('.docx'):
                text = input_docx_text(uploaded_file)

            # Extract details from the text (but do not display the full text)
            details = extract_details_from_text(text)

            # Display extracted details (only these)
            st.write("Extracted Details:")
            st.write(details)

            if any(details.values()):  # Check if any valid data was extracted
                data.append(details)
            else:
                st.warning(f"Invalid data for the uploaded resume.")
        except Exception as e:
            st.error(f"Error processing the uploaded file: {e}")

    elif folder_path:
        # Process resumes from the folder
        try:
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if filename.endswith('.pdf') or filename.endswith('.docx'):
                    try:
                        if filename.endswith('.pdf'):
                            with open(file_path, 'rb') as f:
                                text = input_pdf_text(f)
                        elif filename.endswith('.docx'):
                            text = input_docx_text(file_path)

                        # Extract details (do not show full resume text)
                        details = extract_details_from_text(text)

                        # Display extracted details
                        st.write(f"Extracted Details for {filename}:")
                        st.write(details)

                        if any(details.values()):
                            data.append(details)
                        else:
                            st.warning(f"Invalid data for file {filename}")
                    except Exception as e:
                        st.error(f"Error processing file {filename}: {e}")
        except Exception as e:
            st.error(f"Error accessing folder: {e}")

    else:
        st.error("Please enter a valid folder path or upload a file.")

    # If we have any valid extracted data, display it and save it to CSV and Excel
    if data:
        try:
            df = pd.DataFrame(data)
            save_folder = os.getcwd()
            csv_file_path = os.path.join(save_folder, 'resumes_details.csv')
            excel_file_path = os.path.join(save_folder, 'resumes_details.xlsx')

            df.to_csv(csv_file_path, index=False)
            df.to_excel(excel_file_path, index=False)

            st.header("Extracted Resume Details")
            st.table(df)

            with open(csv_file_path, "rb") as f:
                st.download_button(
                    label="Download CSV File",
                    data=f,
                    file_name='resumes_details.csv',
                    mime='text/csv'
                )

            with open(excel_file_path, "rb") as f:
                st.download_button(
                    label="Download Excel File",
                    data=f,
                    file_name='resumes_details.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

            st.success(f"Resumes processed and saved to CSV and Excel files.")
        except Exception as e:
            st.error(f"Error saving files: {e}")
