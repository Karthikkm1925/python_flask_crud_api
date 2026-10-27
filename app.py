import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore

# ----------------------------------------------------
# 1. Initialize Flask & CORS
# ----------------------------------------------------
app = Flask(__name__)
CORS(app)

# ----------------------------------------------------
# 2. Initialize Firebase Admin SDK & Firestore
# ----------------------------------------------------
cred_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")

if not os.path.exists(cred_path):
    raise FileNotFoundError(f"serviceAccountKey.json not found at {cred_path}")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

# Connect to Cloud Firestore
db = firestore.client()
COLLECTION_NAME = "tasks"

# ----------------------------------------------------
# 3. Base & Health Check
# ----------------------------------------------------
@app.get("/")
def home():
    return "<h1>Flask + Cloud Firestore API</h1><p>Visit /api/health or /api/tasks</p>"

@app.get("/api/health")
def health_check():
    return jsonify({
        "status": "Running",
        "database": "Connected to Cloud Firestore",
        "project": "fir-management-system-46de7"
    }), 200

# ----------------------------------------------------
# 4. READ ALL (Get all tasks from Firestore)
# ----------------------------------------------------
@app.get("/api/tasks")
def get_all_tasks():
    try:
        tasks_ref = db.collection(COLLECTION_NAME).stream()
        tasks = []
        for doc in tasks_ref:
            task = doc.to_dict()
            task["id"] = doc.id
            if "created_at" in task and task["created_at"]:
                task["created_at"] = task["created_at"].isoformat()
            if "updated_at" in task and task["updated_at"]:
                task["updated_at"] = task["updated_at"].isoformat()
            tasks.append(task)
        
        return jsonify({"tasks": tasks, "count": len(tasks)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------
# 5. READ ONE (Get single task by Firestore document ID)
# ----------------------------------------------------
@app.get("/api/tasks/<string:task_id>")
def get_task(task_id):
    try:
        doc = db.collection(COLLECTION_NAME).document(task_id).get()
        if not doc.exists:
            return jsonify({"error": f"Task '{task_id}' not found"}), 404
        
        task = doc.to_dict()
        task["id"] = doc.id
        if "created_at" in task and task["created_at"]:
            task["created_at"] = task["created_at"].isoformat()
        if "updated_at" in task and task["updated_at"]:
            task["updated_at"] = task["updated_at"].isoformat()
            
        return jsonify(task), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------
# 6. CREATE (Add a new task to Firestore)
# ----------------------------------------------------
@app.post("/api/tasks")
def create_task():
    try:
        data = request.get_json()
        if not data or "title" not in data or not data["title"].strip():
            return jsonify({"error": "'title' field is required"}), 400

        new_task = {
            "title": data["title"].strip(),
            "description": data.get("description", ""),
            "completed": data.get("completed", False),
            "priority": data.get("priority", "medium"),
            "created_at": firestore.SERVER_TIMESTAMP
        }

        # Save to Firestore (auto-generates unique document ID)
        doc_ref = db.collection(COLLECTION_NAME).document()
        doc_ref.set(new_task)

        # Return response with generated ID
        new_task["id"] = doc_ref.id
        new_task["created_at"] = "just now"
        return jsonify({"message": "Task created successfully", "task": new_task}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------
# 7. UPDATE (Update task by Firestore document ID)
# ----------------------------------------------------
@app.put("/api/tasks/<string:task_id>")
def update_task(task_id):
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(task_id)
        if not doc_ref.get().exists:
            return jsonify({"error": f"Task '{task_id}' not found"}), 404

        data = request.get_json() or {}
        update_data = {}
        for field in ["title", "description", "completed", "priority"]:
            if field in data:
                update_data[field] = data[field]

        # Automatically track edit timestamp
        update_data["updated_at"] = firestore.SERVER_TIMESTAMP

        doc_ref.update(update_data)

        updated_doc = doc_ref.get().to_dict()
        updated_doc["id"] = task_id
        if "created_at" in updated_doc and updated_doc["created_at"]:
            updated_doc["created_at"] = updated_doc["created_at"].isoformat()
        if "updated_at" in updated_doc and updated_doc["updated_at"]:
            updated_doc["updated_at"] = updated_doc["updated_at"].isoformat()

        return jsonify({"message": "Task updated successfully", "task": updated_doc}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------
# 8. DELETE (Delete task by Firestore document ID)
# ----------------------------------------------------
@app.delete("/api/tasks/<string:task_id>")
def delete_task(task_id):
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(task_id)
        if not doc_ref.get().exists:
            return jsonify({"error": f"Task '{task_id}' not found"}), 404

        doc_ref.delete()
        return jsonify({"message": f"Task '{task_id}' deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------
# Runner
# ----------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
