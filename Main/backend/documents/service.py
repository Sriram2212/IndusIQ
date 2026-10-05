import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import UploadFile


class DocumentService:
    def __init__(self):
        # Resolve project root dynamically
        # file: backend/documents/service.py -> backend -> project_root
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_file_dir)
        project_root = os.path.dirname(backend_dir)
        
        # Check standard sample_data directory locations
        candidate_1 = os.path.join(project_root, "sample_data", "uploads")
        candidate_2 = os.path.join(backend_dir, "sample_data", "uploads")
        candidate_3 = os.path.abspath("sample_data/uploads")
        
        # Default to candidate_1 if project_root has sample_data, else candidate_3
        if os.path.exists(os.path.dirname(candidate_1)):
            self.upload_dir = candidate_1
        elif os.path.exists(os.path.dirname(candidate_2)):
            self.upload_dir = candidate_2
        else:
            self.upload_dir = candidate_3

        os.makedirs(self.upload_dir, exist_ok=True)
        print(f"[DOCUMENT SERVICE] Upload directory resolved to: {self.upload_dir}")

    def get_upload_dir(self) -> str:
        os.makedirs(self.upload_dir, exist_ok=True)
        return self.upload_dir

    def save_file(self, file: UploadFile) -> str:
        """
        Saves uploaded file safely into the upload directory.
        """
        os.makedirs(self.upload_dir, exist_ok=True)
        # Sanitize filename to prevent directory traversal
        clean_filename = os.path.basename(file.filename or "uploaded_document.pdf")
        file_path = os.path.join(self.upload_dir, clean_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"[DOCUMENT SERVICE] Saved file to: {file_path} ({os.path.getsize(file_path)} bytes)")
        return file_path

    def get_file_path(self, filename: str) -> Optional[str]:
        """
        Gets absolute path for a filename if it exists.
        Protects against path traversal attacks.
        """
        clean_filename = os.path.basename(filename)
        file_path = os.path.join(self.upload_dir, clean_filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return file_path
        
        # Fallback check in current working directory sample_data/uploads
        cwd_fallback = os.path.abspath(os.path.join("sample_data", "uploads", clean_filename))
        if os.path.exists(cwd_fallback) and os.path.isfile(cwd_fallback):
            return cwd_fallback

        return None

    def delete_file(self, filename: str) -> bool:
        """
        Deletes a file from the upload directory.
        """
        file_path = self.get_file_path(filename)
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[DOCUMENT SERVICE] Successfully deleted file: {file_path}")
                return True
            except Exception as e:
                print(f"[DOCUMENT SERVICE ERROR] Failed to delete file {file_path}: {e}")
                return False
        return False

    def list_stored_files(self) -> List[Dict[str, Any]]:
        """
        Scans upload folder and returns file metadata.
        """
        if not os.path.exists(self.upload_dir):
            return []
        
        files_info = []
        for fname in os.listdir(self.upload_dir):
            fpath = os.path.join(self.upload_dir, fname)
            if os.path.isfile(fpath):
                size_bytes = os.path.getsize(fpath)
                size_str = (
                    f"{round(size_bytes / (1024 * 1024), 2)} MB"
                    if size_bytes > 1024 * 1024
                    else f"{round(size_bytes / 1024, 2)} KB"
                )
                ext = fname.split(".")[-1].upper() if "." in fname else "OTHER"
                files_info.append({
                    "filename": fname,
                    "path": fpath,
                    "size_bytes": size_bytes,
                    "size": size_str,
                    "extension": ext
                })
        return files_info

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Calculates storage metrics across the uploads directory.
        """
        files = self.list_stored_files()
        total_bytes = sum(f["size_bytes"] for f in files)
        total_mb = round(total_bytes / (1024 * 1024), 2)
        total_kb = round(total_bytes / 1024, 2)
        formatted_size = f"{total_mb} MB" if total_mb >= 1.0 else f"{total_kb} KB"

        pdf_count = sum(1 for f in files if f["extension"] == "PDF")
        docx_count = sum(1 for f in files if f["extension"] in ["DOC", "DOCX"])
        excel_count = sum(1 for f in files if f["extension"] in ["XLS", "XLSX", "CSV"])
        other_count = len(files) - (pdf_count + docx_count + excel_count)

        return {
            "total_documents": len(files),
            "total_bytes": total_bytes,
            "total_size_formatted": formatted_size,
            "pdf_count": pdf_count,
            "docx_count": docx_count,
            "excel_count": excel_count,
            "other_count": other_count,
            "storage_path": self.upload_dir
        }