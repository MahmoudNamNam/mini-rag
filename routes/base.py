from fastapi import FastAPI, APIRouter

base_router = APIRouter()

@base_router.get("/")
def health():
    return {"message": "Welcome to the Mini RAG API"}
