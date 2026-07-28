"""
API HTTP del agente BimBam Buy, pensada para desplegarse en OCI Compute.

Expone:
- GET  /          -> healthcheck simple
- POST /preguntar -> recibe {"pregunta": "..."} y devuelve la respuesta del agente

Ejecutar localmente:
    uvicorn app:app --host 0.0.0.0 --port 8000

En OCI Compute (instancia Linux con puerto 8000 abierto en la Security List):
    uvicorn app:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from pydantic import BaseModel

from agente import build_agent, ask

app = FastAPI(title="Alura Agente - BimBam Buy")

# El agente se construye una sola vez al iniciar el servidor
qa_chain = build_agent()


class Pregunta(BaseModel):
    pregunta: str


@app.get("/")
def home():
    return {
        "status": "ok",
        "mensaje": "Agente BimBam Buy activo. Envía un POST a /preguntar con {'pregunta': '...'}",
    }


@app.post("/preguntar")
def preguntar(payload: Pregunta):
    respuesta = ask(qa_chain, payload.pregunta)
    return {"pregunta": payload.pregunta, "respuesta": respuesta}
