from fastapi import FastAPI

app = FastAPI(title="Credo Health FHIR Migration")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
