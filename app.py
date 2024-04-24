from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import streamlit as st
import os
import tempfile

# Constants
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = "/etc/secrets/service_upload" 

def authenticate():
    # Check if the service account file exists and is accessible
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found at {SERVICE_ACCOUNT_FILE}")
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return creds

def build_drive_service(creds):
    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(service, file_path, file_name, mime_type):
    # Retrieve the parent folder ID from an environment variable
    parent_folder_id = os.getenv('PARENT_FOLDER_ID')
    if not parent_folder_id:
        raise ValueError("Parent folder ID is not set in environment variables.")

    file_metadata = {'name': file_name, 'parents': [parent_folder_id]}
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media).execute()
    return f"https://drive.google.com/file/d/{file['id']}"

def main():
    st.title("📸 Upload Photos for Printing")
    uploaded_files = st.file_uploader("Choose photos to upload 💾", accept_multiple_files=True, type=['jpeg', 'png', 'jpg'])
    
    if uploaded_files:
        creds = authenticate()
        service = build_drive_service(creds)  # Create the Google Drive service object
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            file_name = uploaded_file.name
            mime_type = uploaded_file.type
            link = upload_file_to_drive(service, tmp_path, file_name, mime_type)
            st.success(f"Uploaded successfully! View your photo [here]({link}).")

            os.unlink(tmp_path)  # Clean up the temporary file

if __name__ == "__main__":
    main()

