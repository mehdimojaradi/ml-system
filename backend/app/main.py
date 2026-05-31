from fastapi import FastAPI
app = FastAPI(
    title="Next Gen Bank",
    description="Fully featured banking application built with FastAPI",
)

@app.get("/")
def home():
    return {"message": "Welcome to Next Gen Bank!"}

