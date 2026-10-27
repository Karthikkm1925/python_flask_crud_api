from flask import Flask
from flask import request
app = Flask(__name__)

@app.get("/")
def demo():
    return "Just start..."

@app.get("/api/health")
def health_check():
    return {"Status":"Running", "Application":"Python flask application"}

@app.post("/api/tasks")
def create_task():
    task_data = request.get_json()

    return {"Recieved":task_data},200