# TaskFlow Support Assistant RAG Model

TaskFlow Support Assistant is a RAG-powered knowledge base chatbot for a fictional SaaS project management platform called TaskFlow. It reads Markdown knowledge base articles, embeds them with Google Gemini Embeddings, stores vectors in ChromaDB, retrieves relevant chunks for user questions, generates grounded answers with Gemini 2.5 Flash, and exposes the system through a FastAPI backend.

## Project Structure

```text
RAG_MODEL/
|-- app.py
|-- ingest.py
|-- retrieve.py
|-- rag_chat.py
|-- requirements.txt
|-- .env.example
|-- .env
|-- kb/
|-- chroma_db/
|-- tickets/
|   `-- tickets.json
`-- taskflow_rag/
    |-- chunking.py
    |-- config.py
    |-- embeddings.py
    |-- logging_config.py
    |-- markdown_loader.py
    |-- models.py
    |-- pipeline.py
    |-- ticket_store.py
    `-- vector_store.py
```

## What The System Does

The ingestion pipeline reads all Markdown files from `kb/`, extracts article filenames and Markdown section headings, splits the content into chunks, generates Gemini embeddings, and stores the vectors in a local ChromaDB collection named `taskflow_kb`.

The retrieval layer accepts a user question, creates a query embedding, searches ChromaDB, returns the top matching chunks, and includes metadata such as article, section, source, chunk ID, and similarity score.

The answer generation layer checks retrieval confidence. If confidence is high enough, it sends the retrieved context to Gemini 2.5 Flash and returns a concise support answer with citations. If confidence is low, it skips Gemini and suggests creating a support ticket.

The FastAPI backend exposes the chatbot and ticket system through HTTP endpoints.

## Environment Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Copy the environment example:

```powershell
Copy-Item .env.example .env
```

Set your Gemini API key in `.env`:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001
GEMINI_CHAT_MODEL=gemini-2.5-flash
CHROMA_COLLECTION_NAME=taskflow_kb
CHROMA_PERSIST_DIRECTORY=./chroma_db
KB_DIRECTORY=./kb
```

## Ingest The Knowledge Base

Run:

```powershell
python ingest.py
```

Expected successful output:

```text
Ingestion completed successfully.
Total files processed: 10
Total chunks created: 60
Total vectors stored: 60
```

If vectors already exist, ingestion is skipped to avoid duplicates.

## Test Retrieval

Run:

```powershell
python retrieve.py "How do I invite a team member?"
```

This prints the top matching articles, sections, and scores.

## Test RAG Chat

Interactive mode:

```powershell
python rag_chat.py
```

One-shot mode:

```powershell
python rag_chat.py "How do I invite a team member?"
```

The chatbot retrieves relevant chunks, checks confidence, calls Gemini when confidence is at least `0.70`, and returns an answer with citations.

## Run The FastAPI Backend

Start the server:

```powershell
uvicorn app:app --reload
```

API URL:

```text
http://localhost:8000
```

Swagger docs:

```text
http://localhost:8000/docs
```

## API Endpoints

### GET /health

Returns:

```json
{
  "status": "healthy"
}
```

### POST /chat

Request:

```json
{
  "question": "How do I invite a team member?"
}
```

Response:

```json
{
  "answer": "To invite a team member...",
  "sources": ["invite-team-members.md > Steps"],
  "confidence": 0.72,
  "escalate": false
}
```

### POST /ticket

Request:

```json
{
  "question": "My laptop battery is draining fast",
  "user_name": "Mahaveer",
  "email": "mahaveer@example.com"
}
```

Response:

```json
{
  "ticket_id": "TKT-0001",
  "status": "OPEN",
  "message": "Ticket created successfully"
}
```

### GET /tickets

Response:

```json
[
  {
    "ticket_id": "TKT-0001",
    "status": "OPEN"
  }
]
```

## PowerShell API Testing

Use `Invoke-RestMethod` instead of `curl`, because PowerShell aliases `curl` to `Invoke-WebRequest`.

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8000/chat" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"question":"How do I invite a team member?"}' |
ConvertTo-Json -Depth 5
```

## Notes

- ChromaDB data is stored locally in `chroma_db/`.
- Support tickets are stored locally in `tickets/tickets.json`.
- The RAG response is grounded only in retrieved KB context.
- Low-confidence questions return an escalation response instead of calling Gemini.
- This project is ready to connect to a frontend web application.
