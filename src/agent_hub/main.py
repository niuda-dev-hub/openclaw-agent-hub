from fastapi import FastAPI

app = FastAPI(title="OpenClaw Agent Hub", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "openclaw-agent-hub"}
