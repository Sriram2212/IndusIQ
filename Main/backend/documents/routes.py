from fastapi import APIRouter, UploadFile, File, Header, HTTPException, Body
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
import os
from datetime import datetime

from backend.documents.service import DocumentService
from backend.storage.mongodb_manager import MongoDBManager

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

document_service = DocumentService()
_pipeline_instance = None
_vector_service_instance = None


def get_pipeline():
    global _pipeline_instance
    if _pipeline_instance is None:
        from backend.pipeline.processing_pipeline import ProcessingPipeline
        _pipeline_instance = ProcessingPipeline()
    return _pipeline_instance


def get_vector_service():
    global _vector_service_instance
    if _vector_service_instance is None:
        from backend.services.vector_service import VectorService
        _vector_service_instance = VectorService()
    return _vector_service_instance


def _categorize_filename(filename: str) -> str:
    name_lower = filename.lower()
    if "manual" in name_lower or "guide" in name_lower or "oem" in name_lower:
        return "manual"
    elif "spec" in name_lower or "blueprint" in name_lower or "design" in name_lower or "schematic" in name_lower:
        return "blueprint"
    elif "log" in name_lower or "shift" in name_lower or "telemetry" in name_lower:
        return "log"
    return "report"


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    x_user_role: Optional[str] = Header(None)
):
    """
    Upload a single document, parse knowledge into Neo4j & FAISS, and store metadata in MongoDB.
    RBAC: Engineers and Technicians can upload. Operators have read-only access.
    """
    role = (x_user_role or "engineer").lower()
    if role == "operator":
        raise HTTPException(
            status_code=403,
            detail="Plant Operators have read-only access and cannot upload documents. Please contact Chief Engineer or Technician."
        )

    # 1. Save uploaded file to disk
    file_path = document_service.save_file(file)

    # 2. Run the LangGraph processing pipeline (automatically handles FAISS deduplication & Neo4j graph)
    try:
        pipeline = get_pipeline()
        knowledge = pipeline.process(file_path)
    except Exception as e:
        print(f"[PIPELINE ERROR] Processing failed for {file.filename}: {e}")
        knowledge = []

    # 3. Compute file metadata
    size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    size_str = (
        f"{round(size_bytes / (1024 * 1024), 2)} MB"
        if size_bytes > 1024 * 1024
        else f"{round(size_bytes / 1024, 2)} KB"
    )
    category = _categorize_filename(file.filename)
    file_ext = file.filename.split(".")[-1].upper() if "." in file.filename else "PDF"

    # 4. Save metadata to MongoDB
    doc_id = None
    try:
        db = MongoDBManager()
        existing = db.documents_collection.find_one({"name": file.filename})
        if existing:
            db.documents_collection.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "size": size_str,
                        "size_bytes": size_bytes,
                        "category": category,
                        "file_type": file_ext,
                        "chunks_count": len(knowledge),
                        "uploaded_by_role": role,
                        "uploaded_at": datetime.utcnow(),
                        "status": "Indexed in Neo4j & FAISS"
                    }
                }
            )
            doc_id = str(existing["_id"])
        else:
            ins = db.documents_collection.insert_one({
                "name": file.filename,
                "size": size_str,
                "size_bytes": size_bytes,
                "category": category,
                "file_type": file_ext,
                "chunks_count": len(knowledge),
                "uploaded_by_role": role,
                "uploaded_at": datetime.utcnow(),
                "status": "Indexed in Neo4j & FAISS"
            })
            doc_id = str(ins.inserted_id)
    except Exception as e:
        print(f"[MONGODB ERROR] Failed to record uploaded document metadata: {e}")

    return {
        "id": doc_id,
        "filename": file.filename,
        "name": file.filename,
        "category": category,
        "size": size_str,
        "status": "processed and stored successfully",
        "chunks": len(knowledge),
        "knowledge_extracted": knowledge
    }


@router.post("/upload-batch")
def upload_batch_documents(
    files: List[UploadFile] = File(...),
    x_user_role: Optional[str] = Header(None)
):
    """
    Upload and process multiple documents.
    RBAC: Engineers and Technicians can upload. Operators are restricted.
    """
    role = (x_user_role or "engineer").lower()
    if role == "operator":
        raise HTTPException(
            status_code=403,
            detail="Plant Operators have read-only access and cannot upload documents."
        )

    results = []
    for file in files:
        try:
            res = upload_document(file=file, x_user_role=x_user_role)
            results.append({
                "filename": file.filename,
                "status": "success",
                "data": res
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })

    return {
        "total_uploaded": len(files),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "results": results
    }


@router.get("")
def list_documents(x_user_role: Optional[str] = Header(None)):
    """
    List indexed documents with role-based access control filtering:
    - Engineer: All documents (blueprints, OEM manuals, reports, logs)
    - Technician: Manuals, maintenance reports, shift logs (blueprints restricted)
    - Operator: Operational shift logs and summary reports only (blueprints & OEM manuals restricted)
    """
    role = (x_user_role or "engineer").lower()

    try:
        db = MongoDBManager()
        all_files = db.get_all_documents()
    except Exception as e:
        print(f"[MONGODB ERROR] Failed to read database files: {e}")
        all_files = []

    # Sync with disk if DB is empty or has fewer files
    if not all_files:
        disk_files = document_service.list_stored_files()
        for df in disk_files:
            all_files.append({
                "name": df["filename"],
                "size": df["size"],
                "category": _categorize_filename(df["filename"]),
                "file_type": df["extension"],
                "status": "Stored on Disk"
            })

    if role == "technician":
        filtered = [f for f in all_files if f.get("category") in ["manual", "report", "log"]]
    elif role == "operator":
        filtered = [f for f in all_files if f.get("category") in ["report", "log"]]
    else:  # engineer or admin
        filtered = all_files

    return filtered


@router.get("/stats")
def get_document_stats(x_user_role: Optional[str] = Header(None)):
    """
    Get aggregated storage metrics, document counts, and storage directory information.
    """
    stats = document_service.get_storage_stats()
    try:
        db = MongoDBManager()
        db_docs = db.get_all_documents()
        stats["db_indexed_count"] = len(db_docs)
    except Exception:
        stats["db_indexed_count"] = stats["total_documents"]

    return stats


@router.get("/{filename}/preview")
def preview_document(
    filename: str,
    x_user_role: Optional[str] = Header(None)
):
    """
    Stream document with inline disposition for in-browser PDF preview.
    RBAC: Enforces role permission on document category.
    """
    role = (x_user_role or "engineer").lower()
    category = _categorize_filename(filename)

    if role == "operator" and category in ["blueprint", "manual"]:
        raise HTTPException(
            status_code=403,
            detail="Plant Operators lack clearance to view restricted engineering manuals and blueprints."
        )
    if role == "technician" and category == "blueprint":
        raise HTTPException(
            status_code=403,
            detail="Technicians lack clearance to view proprietary engineering blueprints."
        )

    file_path = document_service.get_file_path(filename)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found on server.")

    media_type = "application/pdf" if filename.lower().endswith(".pdf") else "application/octet-stream"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename=\"{filename}\""}
    )


@router.get("/{filename}/download")
def download_document(
    filename: str,
    x_user_role: Optional[str] = Header(None)
):
    """
    Stream document with attachment disposition for downloading.
    RBAC: Restricts proprietary downloads based on role clearance.
    """
    role = (x_user_role or "engineer").lower()
    category = _categorize_filename(filename)

    if role == "operator" and category in ["blueprint", "manual"]:
        raise HTTPException(status_code=403, detail="Operator role clearance insufficient for downloading engineering assets.")
    if role == "technician" and category == "blueprint":
        raise HTTPException(status_code=403, detail="Technician role clearance insufficient for downloading blueprints.")

    file_path = document_service.get_file_path(filename)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found on server.")

    return FileResponse(
        path=file_path,
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )


@router.delete("/{doc_id}")
def delete_document(
    doc_id: str,
    x_user_role: Optional[str] = Header(None)
):
    """
    Delete a document:
    RBAC: ONLY Chief Engineers (engineer role) have clearance to delete documents and purge vector indexes.
    """
    role = (x_user_role or "engineer").lower()
    if role != "engineer":
        raise HTTPException(
            status_code=403,
            detail=f"Access Denied: Only Chief Engineers ('engineer' role) have clearance to delete documents and purge vector embeddings. Your role is '{role}'."
        )

    doc_name = None
    try:
        db = MongoDBManager()
        doc = db.get_document_by_id(doc_id)
        if not doc:
            doc = db.get_document_by_filename(doc_id)
        
        if doc:
            doc_name = doc.get("name")
            db.delete_document(doc_id=doc.get("_id"))
        else:
            doc_name = doc_id
            db.delete_document(filename=doc_name)
    except Exception as e:
        print(f"[MONGODB ERROR] Error finding/deleting document {doc_id}: {e}")
        doc_name = doc_id

    # Delete physical file from disk
    file_deleted = False
    if doc_name:
        file_deleted = document_service.delete_file(doc_name)

    # Clean up vectors from FAISS
    vectors_removed = 0
    if doc_name:
        try:
            vs = get_vector_service()
            vectors_removed = vs.delete_document_vectors(doc_name)
        except Exception as e:
            print(f"[VECTOR CLEANUP ERROR] Failed to remove vectors for {doc_name}: {e}")

    return {
        "status": "success",
        "message": f"Document '{doc_name}' deleted successfully",
        "file_deleted": file_deleted,
        "vectors_removed": vectors_removed
    }


@router.post("/bulk-delete")
def bulk_delete_documents(
    payload: Dict[str, List[str]] = Body(...),
    x_user_role: Optional[str] = Header(None)
):
    """
    Bulk delete multiple documents by list of IDs or filenames.
    RBAC: Restricted to Chief Engineers.
    """
    role = (x_user_role or "engineer").lower()
    if role != "engineer":
        raise HTTPException(
            status_code=403,
            detail=f"Access Denied: Bulk document deletion requires Chief Engineer ('engineer') clearance."
        )

    doc_ids = payload.get("doc_ids", [])
    results = []

    for doc_id in doc_ids:
        try:
            res = delete_document(doc_id=doc_id, x_user_role=x_user_role)
            results.append(res)
        except Exception as e:
            results.append({"status": "error", "doc_id": doc_id, "error": str(e)})

    return {
        "total_requested": len(doc_ids),
        "results": results
    }