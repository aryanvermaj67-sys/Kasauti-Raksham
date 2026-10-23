from fastapi import FastAPI

app = FastAPI(title="Kasauti")


@app.get("/health")
def health():
    return {"status": "ok"}
