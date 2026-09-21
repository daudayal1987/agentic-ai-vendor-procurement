from fastapi import FastAPI

app = FastAPI(
    title="Enterprise Document Intelligence & Decision Assistant",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "environment": "local",
        "day": 2
    }