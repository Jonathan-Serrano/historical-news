# Historical News

A full-stack web application built with:

- Vue.js (TypeScript + Tailwind) frontend
- Flask backend (Python)
- Local LLMs via [Ollama](https://ollama.com/)
- Knowledge grounding using [Neo4j](https://neo4j.com/)
- LangChain-powered GenAI applications with open-source [LLaMA](https://ollama.com/library/llama3) models

---

## Prerequisites

- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/downloads/) (v3.10+)
- [Ollama](https://ollama.com/download)
- [Neo4j Desktop or Aura](https://neo4j.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

---

## Getting Started

### 1. Clone the Repository
### 2. Set up Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate         # On Windows
# Or: source venv/bin/activate  (Linux/macOS)

pip install -r requirements.txt
python app.py
```

```bash
# Remember to download OLLAMA at https://ollama.com/download
ollama serve
ollama pull llama3.2
ollama pull nomic-embed-text
```

```
python neo4j_loader.py
```

```bash
cd backend
docker compose up -d
```

If you are using Colima, do these steps prior:
```bash
brew install docker-compose
colima start
```

### 3. Set up Frontend 
```bash
cd frontend
npm install
npm run dev
```
### 4. Set up environment variables
- Create a `.env` file in the `backend` directory.
- Add the following variables:

    ```env
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=your_password

    LLM_MODEL=llama3.2
    PORT=5000
    ```

- Create a `.env` file in the `frontend` directory.
- Add the following variable:

```env
VITE_API_URL=http://127.0.0.1:5000
``` 

### Closing the project:
```bash
docker compose down
colima stop # If using Colima
```
