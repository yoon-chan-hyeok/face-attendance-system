"""
File processing utilities
"""
import os
import shutil
import uuid
import numpy as np
from fastapi import UploadFile

class FileUtils:
    """File processing utility class"""
    
    @staticmethod
    def save_upload_file(upload_file: UploadFile, destination_dir: str = "data/images") -> str:
        """
        Save uploaded file to specified directory temporarily
        
        Args:
            upload_file: Uploaded file object
            destination_dir: Directory path to save
            
        Returns:
            Full path of saved file
        """
        # Create directory if not exists
        os.makedirs(destination_dir, exist_ok=True)
        
        # Generate unique filename (prevent collision)
        print("file_extension: ", upload_file)

        # Extract extension from uploaded file
        file_extension = upload_file.filename.split(".")[-1] if "." in upload_file.filename else "jpg"

        # Generate unique filename: temp_unique_id.extension
        unique_filename = f"temp_{uuid.uuid4()}.{file_extension}"

        # Create file path: data/images/unique_filename
        file_path = os.path.join(destination_dir, unique_filename)
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
            print(f"[FileUtils] Image temporarily saved: {file_path}")
            return file_path
        except Exception as e:
            print(f"[FileUtils] File save failed: {e}")
            raise IOError(f"Cannot save file: {e}")

    @staticmethod
    def delete_file(file_path: str):
        """
        Delete file
        
        Args:
            file_path: File path to delete
        """
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[FileUtils] File deleted: {file_path}")
            except Exception as e:
                print(f"[FileUtils] File deletion failed: {e}")

    @staticmethod
    def save_vector_to_npy(vector: list, name: str, destination_dir: str = "data/encodings") -> str:
        """
        Save vector list to .npy file
        
        Args:
            vector: Vector list to save
            name: Name (for filename generation)
            destination_dir: Directory to save
            
        Returns:
            Saved .npy file path
        """
        os.makedirs(destination_dir, exist_ok=True)
        
        # Generate filename: {employee_id}_{uuid}.npy
        filename = f"{name}_{uuid.uuid4()}.npy"
        file_path = os.path.join(destination_dir, filename)
        
        try:
            # Convert list to numpy array and save
            np_vector = np.array(vector)
            np.save(file_path, np_vector)
            print(f"[FileUtils] Vector .npy saved: {file_path} (shape: {np_vector.shape})")            
            return file_path
        except Exception as e:
            print(f"[FileUtils] Vector save failed: {e}")
            raise IOError(f"Cannot save vector: {e}")
