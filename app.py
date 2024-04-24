import os
import tempfile
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import streamlit as st

# Constants for Google API
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = "/etc/secrets/service_upload" 
PARENT_FOLDER_ID = os.getenv('PARENT_FOLDER_ID')

def authenticate():
    """Authenticate and return the Google Drive service object."""
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    return service

def get_or_create_folder(service, folder_name, parent_id):
    """Get the folder ID if exists, or create it if not."""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = response.get('files', [])
    if not files:
        file_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    return files[0]['id']

def upload_photo(service, file_path, folder_id):
    """Upload a photo to a specified folder on Google Drive."""
    file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
    media = MediaFileUpload(file_path, mimetype='image/jpeg')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file['id']

def main():
    st.title("📸 Upload Photos for Printing")
    user_name = st.text_input("Enter your name:")
    if user_name:
        service = authenticate()
        user_folder_id = get_or_create_folder(service, user_name, PARENT_FOLDER_ID)
        
        # Define dimensions and create sections for each
        dimensions = ["10x15", "13x18", "15x20"]
        for dimension in dimensions:
            with st.expander(f"Upload photos for {dimension}:"):
                uploaded_files = st.file_uploader(f"Choose photos of size {dimension}", accept_multiple_files=True, type=['jpeg', 'jpg', 'png'], key=dimension)
                if uploaded_files:
                    dimension_folder_id = get_or_create_folder(service, dimension, user_folder_id)
                    for uploaded_file in uploaded_files:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        file_id = upload_photo(service, tmp_path, dimension_folder_id)
                        st.success(f"Uploaded {uploaded_file.name} successfully for {dimension} dimension! ")
                        os.unlink(tmp_path)  # Clean up the temporary file

if __name__ == "__main__":
    main()


