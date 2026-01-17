# Richmond Policy Assistant: Agentic RAG Chatbot

![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![AWS Bedrock](https://img.shields.io/badge/AWS_Bedrock-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-4E42E4?style=for-the-badge&logo=chromadb&logoColor=white)

An intelligent, production-ready **Agentic RAG** (Retrieval-Augmented Generation) system designed to provide students, faculty, and staff with accurate answers from the official University of Richmond policy manual.

## Overview

The Richmond Policy Assistant goes beyond simple search. It utilizes a **Tool-Calling Agent** architecture that allows the LLM to autonomously decide when to query the policy database, how to rephrase user questions for better retrieval, and how to verify information across multiple steps.

### Key Features
- **Agentic Reasoning**: Uses `AgentExecutor` to handle complex multi-turn queries and autonomous tool selection.
- **Semantic Search**: Vectorized retrieval via ChromaDB for high-relevance policy extraction.
- **Persistent Memory**: Session-aware chat history stored in a SQL-backed database (SQLite) for contextual follow-up questions.
- **Modern UI**: A premium, responsive Next.js interface inspired by dark-mode productivity tools.
- **Source Attributions**: Every policy answer includes direct citations to the original document source.

---

## Architecture

The system follows a modern decoupled architecture:

1.  **Frontend (Next.js)**: A React-based SPA that handles real-time markdown rendering and session management.
2.  **Backend (FastAPI)**: Asynchronous API serving as the orchestration layer for the LangChain agent.
3.  **Inference (AWS Bedrock)**: Powered by Claude (via Amazon Bedrock) for high-reasoning tool usage.
4.  **Vector Store (ChromaDB)**: Stores embeddings of the Richmond Policy Manual for semantic retrieval.
5.  **Persistence Layer**: SQL storage for maintains `SQLChatMessageHistory` across user sessions.

---

## Technology Stack

- **Frameworks**: FastAPI (Python), Next.js 15 (TypeScript)
- **AI/LLM**: LangChain, Amazon Bedrock (Claude 3 / 3.5)
- **Vector Database**: ChromaDB
- **Database**: SQLite (SQLAlchemy via LangChain)
- **Styling**: Tailwind CSS, Lucide Icons

---

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- AWS Credentials (with Bedrock access)
- ChromaDB API Key/Access

### 1. Backend Configuration
Navigate to the root directory:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# Install dependencies
pip install fastapi uvicorn python-dotenv boto3 chromadb langchain langchain-aws langchain-community pydantic
```

Create a `.env` file in the root:
```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
CHROMA_API_KEY=your_chroma_key
CHROMA_TENANT=your_tenant
CHROMA_DATABASE=your_db
CHROMA_COLLECTION=richmond_policies
DATABASE_URL=sqlite:///./chat_memory.db
```

### 2. Frontend Configuration
Navigate to the `frontend` directory:
```bash
cd frontend
npm install
```

### 3. Running the Project
**Start Backend (Port 8005):**
```bash
# From root
uvicorn app.main:app --reload --port 8005
```

**Start Frontend (Port 3000):**
```bash
# From /frontend
npm run dev
```

---

## Usage

1.  Open [http://localhost:3000](http://localhost:3000).
2.  Start a new chat session.
3.  Ask policy-related questions such as:
    - *"What is the university's drug policy?"*
    - *"Can you explain the academic integrity rules for group projects?"*
    - *"What are the catering requirements for student events?"*

---

## Security & Privacy
- **Data Isolation**: Each user session is isolated via a unique `session_id`.
- **Credential Management**: Environment variables are used to ensure no API keys are hardcoded.
- **Filtering**: The agent is prompted specifically to avoid speculating and only use provided policy context.

---

## Roadmap
- [ ] Integration with Slack/Microsoft Teams.
- [ ] Support for PDF/Document upload and instant indexing.
- [ ] Admin dashboard for monitoring common policy queries.
- [ ] Evaluation suite using Ragas to measure retrieval accuracy.

---

## License
Distributed under the MIT License. See `LICENSE` for more information.

---

**Developed with ❤️ for the University of Richmond Community.**