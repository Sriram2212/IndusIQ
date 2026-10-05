from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import hashlib
from backend.config.settings import MONGODB_URI, MONGODB_DB_NAME

class MongoDBManager:
    def __init__(self, uri=None, db_name=None):
        self.uri = uri or MONGODB_URI or "mongodb://localhost:27017"
        self.db_name = db_name or MONGODB_DB_NAME or "industrial_intelligence"
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.history_collection = self.db["chat_history"]
        self.sessions_collection = self.db["chat_sessions"]
        self.users_collection = self.db["users"]
        self.documents_collection = self.db["documents"]

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def seed_users(self):
        """
        Seeds default user accounts into the users collection if empty.
        """
        if self.users_collection.count_documents({}) == 0:
            default_users = [
                {
                    "username": "kannan",
                    "password_hash": self.hash_password("engineer123"),
                    "role": "engineer",
                    "full_name": "R. Kannan (Chief Eng.)"
                },
                {
                    "username": "suriya",
                    "password_hash": self.hash_password("tech123"),
                    "role": "technician",
                    "full_name": "Suriya (Technician)"
                },
                {
                    "username": "operator1",
                    "password_hash": self.hash_password("operator123"),
                    "role": "operator",
                    "full_name": "Operator 1"
                }
            ]
            self.users_collection.insert_many(default_users)
            print("[MONGODB] Seeded default users successfully.")

    def get_user(self, username: str) -> dict:
        user = self.users_collection.find_one({"username": username})
        if user:
            user["_id"] = str(user["_id"])
        return user


    def save_chat_message(self, session_id: str, role: str, content: str, response_data: dict = None):
        """
        Saves a chat message (user or assistant) to MongoDB.
        Also updates/creates the chat session metadata (e.g. title, last_updated).
        """
        message_doc = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
            "response_data": response_data or {}
        }
        self.history_collection.insert_one(message_doc)

        # Upsert session info
        # If it's a user message, we can set it as the title if the session doesn't have one yet
        session = self.sessions_collection.find_one({"session_id": session_id})
        if not session:
            title = content[:50] + "..." if len(content) > 50 else content
            self.sessions_collection.insert_one({
                "session_id": session_id,
                "title": title,
                "created_at": datetime.utcnow(),
                "last_updated": datetime.utcnow()
            })
        else:
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"last_updated": datetime.utcnow()}}
            )

    def get_chat_history(self, session_id: str):
        """
        Retrieves all messages for a session, sorted by timestamp.
        """
        messages = list(self.history_collection.find({"session_id": session_id}).sort("timestamp", 1))
        for msg in messages:
            msg["_id"] = str(msg["_id"])
            if "timestamp" in msg:
                msg["timestamp"] = msg["timestamp"].isoformat()
        return messages

    def list_chat_sessions(self):
        """
        Lists all chat sessions, sorted by last_updated descending.
        Includes message_count for each session.
        """
        sessions = list(self.sessions_collection.find().sort("last_updated", -1))
        for s in sessions:
            s["_id"] = str(s["_id"])
            if "created_at" in s:
                s["created_at"] = s["created_at"].isoformat()
            if "last_updated" in s:
                s["last_updated"] = s["last_updated"].isoformat()
            # Add message count
            try:
                s["message_count"] = self.history_collection.count_documents(
                    {"session_id": s["session_id"]}
                )
            except Exception:
                s["message_count"] = 0
        return sessions

    def delete_session(self, session_id: str):
        """
        Deletes a session and its message history.
        """
        self.sessions_collection.delete_one({"session_id": session_id})
        self.history_collection.delete_many({"session_id": session_id})

    def get_all_documents(self) -> list:
        docs = list(self.documents_collection.find().sort("uploaded_at", -1))
        for d in docs:
            d["_id"] = str(d["_id"])
            if "uploaded_at" in d and isinstance(d["uploaded_at"], datetime):
                d["uploaded_at"] = d["uploaded_at"].isoformat()
        return docs

    def get_document_by_id(self, doc_id: str) -> dict:
        try:
            doc = self.documents_collection.find_one({"_id": ObjectId(doc_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                if "uploaded_at" in doc and isinstance(doc["uploaded_at"], datetime):
                    doc["uploaded_at"] = doc["uploaded_at"].isoformat()
            return doc
        except Exception:
            return None

    def get_document_by_filename(self, filename: str) -> dict:
        doc = self.documents_collection.find_one({"name": filename})
        if doc:
            doc["_id"] = str(doc["_id"])
            if "uploaded_at" in doc and isinstance(doc["uploaded_at"], datetime):
                doc["uploaded_at"] = doc["uploaded_at"].isoformat()
        return doc

    def delete_document(self, doc_id: str = None, filename: str = None) -> bool:
        """
        Deletes a document from MongoDB by ObjectId or name.
        """
        query = {}
        if doc_id:
            try:
                query["_id"] = ObjectId(doc_id)
            except Exception:
                query["_id"] = doc_id
        elif filename:
            query["name"] = filename
        else:
            return False

        result = self.documents_collection.delete_one(query)
        return result.deleted_count > 0

    def bulk_delete_documents(self, doc_ids: list) -> int:
        """
        Deletes multiple documents by ID list.
        """
        obj_ids = []
        for d in doc_ids:
            try:
                obj_ids.append(ObjectId(d))
            except Exception:
                pass
        result = self.documents_collection.delete_many({"_id": {"$in": obj_ids}})
        return result.deleted_count

