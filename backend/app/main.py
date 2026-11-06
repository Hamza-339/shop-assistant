from fastapi import FastAPI

app = FastAPI()


@app.get("/api")
def api_root() -> dict[str, str]:
    return {"status": "ok"}
