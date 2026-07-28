# Alura Agente – BimBam Buy 🤖

Agente de inteligencia artificial que responde preguntas en lenguaje natural sobre la
**Política de Reembolsos y Devoluciones de BimBam Buy** (e-commerce), sin que la persona
usuaria tenga que abrir el PDF. Proyecto final del programa ONE (IA for Tech).

## 1. Descripción general

BimBam Buy es un e-commerce con operación en LATAM. Su equipo de soporte pierde tiempo
buscando información dentro de políticas internas extensas (32 secciones) cada vez que
necesita resolver una consulta de un cliente. Este agente indexa el documento y permite
hacer preguntas directas (por ejemplo, plazos, condiciones de elegibilidad o costos de
devolución) y recibir la respuesta exacta, citada desde el propio documento.

## 2. Arquitectura de la solución

Se implementó un patrón **RAG (Retrieval Augmented Generation)** con LangChain:

```
Pregunta del usuario
        │
        ▼
┌───────────────────┐      ┌──────────────────────┐      ┌───────────────────┐
│  PDF (PyPDFLoader) │ ───▶ │  Chunking + Embeddings │ ───▶ │  Índice vectorial │
│  politica_...pdf   │      │  (Cohere embed-v3)     │      │      FAISS        │
└───────────────────┘      └──────────────────────┘      └─────────┬─────────┘
                                                                     │ top-k fragmentos
                                                                     ▼
                                                          ┌────────────────────┐
                                                          │  LLM Cohere         │
                                                          │  (command-r-plus)   │
                                                          └─────────┬──────────┘
                                                                     ▼
                                                            Respuesta en lenguaje
                                                                  natural
```

1. **Carga del documento**: `PyPDFLoader` (pypdf) lee el PDF y lo convierte en texto.
2. **Fragmentación**: `RecursiveCharacterTextSplitter` divide el texto en chunks de ~1000
   caracteres con solapamiento, para no perder contexto entre secciones.
3. **Embeddings + índice vectorial**: cada chunk se convierte en un vector con
   `CohereEmbeddings` (modelo `embed-multilingual-v3.0`) y se guarda en un índice **FAISS**
   en memoria.
4. **Recuperación (retrieval)**: ante una pregunta, se buscan los 4 fragmentos más
   similares semánticamente.
5. **Generación**: `ChatCohere` (`command-r-plus`) recibe la pregunta + los fragmentos
   recuperados y redacta la respuesta final.
6. **Exposición pública**: `app.py` envuelve el agente en una API con **FastAPI**, lista
   para desplegarse en una instancia de **OCI Compute**.

## 3. Tecnologías utilizadas

| Componente          | Herramienta                          |
|----------------------|--------------------------------------|
| Lenguaje             | Python 3.11                          |
| Orquestación del agente | LangChain                          |
| Lectura del documento | PyPDF (PDF)                         |
| Modelo de lenguaje (LLM) | Cohere `command-r-plus`          |
| Embeddings            | Cohere `embed-multilingual-v3.0`    |
| Base vectorial        | FAISS (en memoria)                   |
| API / Deploy          | FastAPI + Uvicorn                    |
| Nube                  | Oracle Cloud Infrastructure (OCI Compute) |

## 4. Estructura del repositorio

```
.
├── agente.py                              # Lógica del agente (RAG con LangChain + Cohere)
├── app.py                                 # API FastAPI para exponer el agente (deploy en OCI)
├── requirements.txt                       # Dependencias del proyecto
├── .env.example                           # Plantilla de variables de entorno
├── data/
│   └── politica_reembolsos_bimbam_buy.pdf # Documento fuente (descargar, ver sección 5)
└── README.md
```

## 5. Cómo ejecutar el proyecto localmente

```bash
# 1. Clonar el repositorio
git clone <URL_DE_TU_REPOSITORIO>
cd <tu-repositorio>

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env y colocar tu COHERE_API_KEY (gratis en https://dashboard.cohere.com/api-keys)

# 4. Descargar el documento fuente
mkdir -p data
# Descargar "Política de Reembolsos y Devoluciones de BimBam Buy.pdf" y guardarlo como:
# data/politica_reembolsos_bimbam_buy.pdf

# 5a. Probar el agente por consola
python agente.py

# 5b. O levantar la API local
uvicorn app:app --reload
# Luego, POST a http://localhost:8000/preguntar con body: {"pregunta": "..."}
```

> 💡 Tip: para prototipar rápido sin instalar nada localmente, se puede correr este mismo
> código en **Google Colab**, instalando las dependencias con `!pip install -r requirements.txt`.

## 6. Ejemplos de preguntas y respuestas

| Pregunta | Respuesta del agente |
|---|---|
| ¿Cuántos días tiene un cliente para solicitar una devolución por retracto? | El cliente puede solicitar la devolución por retracto dentro de los **10 días corridos** posteriores a la recepción del pedido, siempre que el producto cumpla los requisitos de elegibilidad. |
| ¿Cuánto tarda en procesarse un reembolso ya aprobado? | Entre **5 y 10 días hábiles**, dependiendo del método de pago y del país de origen de la compra. |
| Si el error fue de BimBam Buy, ¿quién paga el envío de la devolución? | Si el error es atribuible a BimBam Buy, la recolección o devolución **no tiene costo para el cliente**. |
| Un pedido llega con un accesorio faltante, ¿qué corresponde? | Se evalúa un **reembolso parcial** o el envío del faltante, según validación interna, ya que se trata de un "faltante parcial". |
| ¿En cuánto tiempo debo reportar un producto dañado al recibirlo? | Dentro de las **48 horas** posteriores a la entrega, adjuntando evidencia fotográfica o video. |

*(Respuestas verificadas contra el contenido real del documento fuente.)*

## 7. Deploy en Oracle Cloud Infrastructure (OCI)

Pasos sugeridos para desplegar `app.py` en una instancia de **OCI Compute**:

1. Crear una instancia Compute (Always Free: `VM.Standard.E2.1.Micro` o `Ampere A1`), imagen
   Ubuntu, y guardar la clave SSH.
2. Abrir el puerto de la API (8000) en la **Security List / Network Security Group** de la
   VCN, y también en el firewall del sistema operativo (`sudo ufw allow 8000`).
3. Conectarse por SSH y preparar el entorno:
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv git
   git clone <URL_DE_TU_REPOSITORIO>
   cd <tu-repositorio>
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env   # completar COHERE_API_KEY
   mkdir -p data          # subir el PDF a data/
   ```
4. Levantar la API (para dejarla corriendo en segundo plano, usar `nohup`, `tmux` o un
   servicio `systemd`):
   ```bash
   nohup uvicorn app:app --host 0.0.0.0 --port 8000 &
   ```
5. Verificar acceso público: `http://<IP_PUBLICA_DE_LA_INSTANCIA>:8000`

**Evidencia del deploy:**
- URL pública: `<COMPLETAR_CON_LA_URL_DE_OCI>`
- Captura de pantalla: `<ADJUNTAR_SCREENSHOT_AQUI>`

## 8. Checklist de entrega (Challenge Alura Agente)

- [x] Repositorio en GitHub con historial de commits y estructura organizada
- [x] README con descripción, arquitectura, tecnologías, instrucciones y ejemplos de Q&A
- [x] Agente funcional que responde preguntas sobre un documento (PDF)
- [ ] Evidencia del deploy en OCI (URL pública y/o captura de pantalla) — completar antes de
      enviar el challenge
