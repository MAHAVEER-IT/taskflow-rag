# Project Prompts

This file records the main prompts used to build the TaskFlow Support Assistant RAG project.

## 1. Knowledge Base Articles

Generate production-quality Markdown documentation for a fictional SaaS project management platform called TaskFlow.

Required articles:

```text
account-creation.md
reset-password.md
invite-team-members.md
create-project.md
manage-user-roles.md
billing-and-subscriptions.md
notifications.md
file-upload.md
integrations.md
troubleshooting.md
```

Each article should include:

```text
# Title
## Overview
## Steps
## Important Notes
## Troubleshooting
## FAQ
```

The articles should be clear, customer-support focused, non-technical, realistic for SaaS workflows, and suitable as a RAG knowledge source.

## 2. Ingestion Pipeline

Build a Python ingestion pipeline that:

```text
KB Files
  |
Markdown Loader
  |
Chunking
  |
Gemini Embeddings
  |
ChromaDB Storage
```

Requirements:

- Read all `.md` files recursively from `kb/`.
- Extract article filename and Markdown section headings.
- Use LangChain `RecursiveCharacterTextSplitter`.
- Use `chunk_size = 1000`.
- Use `chunk_overlap = 200`.
- Generate embeddings using Google Gemini Embeddings.
- Store vectors in ChromaDB using `persist_directory="./chroma_db"`.
- Use collection name `taskflow_kb`.
- Store metadata: article, section, source, and chunk ID.
- Skip duplicate ingestion if vectors already exist.
- Print total files processed, total chunks created, and total vectors stored.
- Add logging and exception handling.

## 3. Modularization

Refactor the ingestion code so everything is not inside one large file.

Create a modular architecture under `taskflow_rag/`, with separate responsibilities for:

- configuration
- Markdown loading
- chunking
- embeddings
- ChromaDB vector store access
- pipeline orchestration
- logging
- shared models

Also remove duplicate Markdown files outside the `kb/` folder.

## 4. Retrieval And Gemini Response Layer

Create:

```text
retrieve.py
rag_chat.py
```

Workflow:

```text
User Question
  |
Generate Query Embedding
  |
Search ChromaDB
  |
Retrieve Top 3 Chunks
  |
Build Context
  |
Send Context to Gemini
  |
Generate Answer
  |
Return Citation
```

`retrieve.py` should:

- connect to existing ChromaDB
- use the existing Gemini embedding model
- accept a user question
- return top 3 chunks
- include content, article, section, source, chunk ID, and score
- print article, section, and score

`rag_chat.py` should:

- use Gemini 2.5 Flash
- retrieve chunks
- build context
- use a grounded support prompt
- answer only from context
- cite article and section
- use a confidence threshold of `0.70`
- skip Gemini and suggest escalation when confidence is low
- support interactive CLI mode
- support one-shot CLI mode

Prompt template:

```text
You are a customer support assistant for TaskFlow.

Rules:
1. Answer ONLY using provided context.
2. Do not make up information.
3. If information is missing, say you cannot find it.
4. Always cite article and section.
5. Be concise and professional.

Context:
{retrieved_chunks}

Question:
{user_question}
```

## 5. FastAPI Backend And Ticket Creation API

Expose the working RAG engine through FastAPI and implement ticket creation.

Create:

```text
app.py
tickets/tickets.json
```

Endpoints:

```text
GET /health
POST /chat
POST /ticket
GET /tickets
```

`POST /chat` should:

- accept a question
- call the existing retrieval and Gemini response logic
- return answer, sources, confidence, and escalation status

`POST /ticket` should:

- accept question, user name, and email
- generate ticket IDs like `TKT-0001`
- store tickets in `tickets/tickets.json`
- set status to `OPEN`
- store created timestamp

`GET /tickets` should:

- return ticket ID and status for each ticket

Additional requirements:

- FastAPI
- Pydantic validation
- uvicorn
- python-dotenv
- CORS support
- logging
- exception handling
- type hints
- clean architecture

Startup command:

```powershell
uvicorn app:app --reload
```

Swagger docs:

```text
http://localhost:8000/docs
```

## 6. Current Verified Status

The system has been verified through the terminal:

```text
Ingestion completed successfully.
Total files processed: 10
Total chunks created: 60
Total vectors stored: 60
```

The RAG CLI successfully answered:

```text
How do I invite a team member?
```

The FastAPI health endpoint returned:

```json
{
  "status": "healthy"
}
```

The `/chat` endpoint returned a valid answer. PowerShell may display long fields with `...`, so use `ConvertTo-Json -Depth 5` to inspect the full response.
