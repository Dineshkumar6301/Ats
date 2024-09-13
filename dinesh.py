import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import pandas as pd
import docx2txt
import re

# Load environment variables
load_dotenv()

def app():
    # Configure Google Gemini API
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    # Prompt for Gemini API
    input_prompt = """
    "Act as a highly skilled and experienced Application Tracking System (ATS) with deep expertise in the technology field, including software engineering, data science, data analysis, and big data engineering. Your task is to extract the following details from the provided resume:
    - Name
    - Phone No.
    - Email Id
    - Job Title
    - Current Company
    - Skills
    - Location

    resume: {text}

    If any detail is not present in the resume, return 'Null' for that field."
    """

    # Function to get response from Gemini API
    def get_gemini_response(input_text):
        model = genai.GenerativeModel('gemini-pro')
        try:
            response = model.generate_content(input_text)
            return response.text
        except Exception as e:
            print(f"Error processing input: {e}")
            return None

    # Function to extract text from PDF
    def input_pdf_text(uploaded_file):
        if uploaded_file is not None:
            reader = pdf.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        else:
            raise FileNotFoundError("No file uploaded")

    # Function to extract text from DOCX
    def input_docx_text(uploaded_file):
        return docx2txt.process(uploaded_file)

    # Function to clean and extract data
    def clean_extracted_data(response):
        response = re.sub(r"'", '"', response)
        response = response.replace('\n', ' ')

        # Extract each field using regex
        name = re.search(r"Name:\s*(.*?)( - |$)", response)
        phone = re.search(r"Phone No.\s*(.*?)( - |$)", response)
        email = re.search(r"Email Id:\s*(.*?)( - |$)", response)
        job_title = re.search(r"Job Title:\s*(.*?)( - |$)", response)
        current_company = re.search(r"Current Company:\s*(.*?)( - |$)", response)
        skills = re.search(r"Skills:\s*(.*?)( - |$)", response)
        location = re.search(r"Location:\s*(.*?)( - |$)", response)

        return {
            'Name': name.group(1).strip() if name else 'Null',
            'Phone Number': phone.group(1).strip() if phone else 'Null',
            'Email ID': email.group(1).strip() if email else 'Null',
            'Job Title': job_title.group(1).strip() if job_title else 'Null',
            'Current Company': current_company.group(1).strip() if current_company else 'Null',
            'Skills': skills.group(1).strip() if skills else 'Null',
            'Location': location.group(1).strip() if location else 'Null'
        }

    # Function to save full data to Excel
    def save_full_data_to_excel(data, file_name):
        df = pd.DataFrame(data)
        df.to_excel(file_name, index=False)

    # Function to prepare UI data
    def prepare_ui_data(full_data_list):
        return [
            {
                'Name': item['Name'],
                'Phone Number': item['Phone Number'],
                'Email ID': item['Email ID'],
                'Location': item['Location']
            }
            for item in full_data_list
        ]

    # Streamlit app
    st.title("ATS")

    # Option to choose between single file and folder upload
    upload_option = st.radio("Choose Upload Option", ["Single Resume Upload", "Folder Upload"])

    if upload_option == "Single Resume Upload":
        uploaded_file = st.file_uploader("Choose a file (PDF or DOCX)", type=['pdf', 'docx'])

        if uploaded_file is not None:
            text = ""
            if uploaded_file.type == 'application/pdf':
                text = input_pdf_text(uploaded_file)
            elif uploaded_file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                text = input_docx_text(uploaded_file)

            if text:
                formatted_prompt = input_prompt.format(text=text)
                response = get_gemini_response(formatted_prompt)

                if response:
                    # Clean and extract data
                    extracted_data = clean_extracted_data(response)

                    # Save full data to Excel
                    df_full = pd.DataFrame([extracted_data])
                    df_full.to_excel('single_resume_output.xlsx', index=False)

                    # Display only required data on UI
                    ui_data = pd.DataFrame([{
                        'Name': extracted_data['Name'],
                        'Phone Number': extracted_data['Phone Number'],
                        'Email ID': extracted_data['Email ID'],
                        'Location': extracted_data['Location']
                    }])
                    st.write(ui_data)
                    st.success("Extracted data has been saved to single_resume_output.xlsx")

    elif upload_option == "Folder Upload":
        folder_path = st.text_input("Enter Folder Path", "D:/Resumes")
        submit = st.button("Submit")

        if submit:
            if folder_path:
                file_list = [f for f in os.listdir(folder_path) if f.endswith('.pdf') or f.endswith('.docx')]
                total_files = len(file_list)
                full_data_list = []

                if total_files == 0:
                    st.warning("No PDF or DOCX files found in the provided folder path.")
                else:
                    progress_bar = st.progress(0)
                    progress_text = st.empty()

                    for idx, filename in enumerate(file_list):
                        file_path = os.path.join(folder_path, filename)
                        try:
                            if filename.endswith('.pdf'):
                                text = input_pdf_text(file_path)
                            elif filename.endswith('.docx'):
                                text = input_docx_text(file_path)

                            formatted_prompt = input_prompt.format(text=text)
                            response = get_gemini_response(formatted_prompt)

                            if response:
                                # Clean and extract data
                                extracted_data = clean_extracted_data(response)
                                full_data_list.append(extracted_data)

                            # Update progress bar
                            progress_percentage = (idx + 1) / total_files * 100
                            progress_bar.progress(int(progress_percentage))
                            progress_text.text(f"Processing file {idx + 1} of {total_files} files...")

                        except Exception as e:
                            print(f"Error processing file {filename}: {e}")
                            st.error(f"Error processing file {filename}: {e}")

                    # Prepare UI data (only selected fields)
                    ui_data = prepare_ui_data(full_data_list)

                    # Display only UI-specific columns
                    st.write(pd.DataFrame(ui_data))

                    # Save full data to Excel (backend storage)
                    save_full_data_to_excel(full_data_list, 'folder_resume_output.xlsx')
                    st.success("Extracted data from folder has been saved to folder_resume_output.xlsx")
            else:
                st.error("Please enter a valid folder path.")

# Run the app
if __name__ == "__main__":
    app()
