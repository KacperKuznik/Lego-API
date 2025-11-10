from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
from dotenv import load_dotenv
from fastapi import UploadFile
import os
import uuid
from typing import List
import mimetypes

load_dotenv()

STORAGE_CONNECTION_STRING = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "legoset-images"

class BlobStorageManager:
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        self.container_client = self.blob_service_client.get_container_client(CONTAINER_NAME)
        self._ensure_container_exists()

    def _ensure_container_exists(self):
        try:
            self.blob_service_client.create_container(CONTAINER_NAME, public_access="blob")
        except ResourceExistsError:
            pass

    def upload_image(self, file: UploadFile, legoset_id: str) -> str:
        # Get file extension
        _, extension = os.path.splitext(file.filename)
        
        # Generate unique blob name
        blob_name = f"{legoset_id}/{str(uuid.uuid4())}{extension}"
        
        # Get content type
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        
        # Upload directly from memory
        self.container_client.upload_blob(
            name=blob_name,
            data=file.file,
            content_type=content_type,
            overwrite=True
        )
        
        return blob_name

    def upload_legoset_images(self, files: List[UploadFile], legoset_id: str) -> List[str]:
        uploaded_files = []
        for file in files:
            try:
                blob_name = self.upload_image(file, legoset_id)
                uploaded_files.append(blob_name)
            except Exception as e:
                print(f"Failed to upload {file.filename}: {e}")
        return uploaded_files
    
    def get_image_url(self, blob_name: str) -> str:
        blob_client = self.container_client.get_blob_client(blob_name)
        return blob_client.url

    def delete_image(self, blob_name: str):
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_client.delete_blob()

    def delete_legoset_images(self, legoset_id: str):
        prefix = f"{legoset_id}/"
        blobs = self.container_client.list_blobs(name_starts_with=prefix)
        for blob in blobs:
            self.delete_image(blob.name)