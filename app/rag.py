import os
import boto3
import chromadb
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.chat_message_histories import SQLChatMessageHistory

# -------------------------
# 1) Chroma setup (Optimized Singleton)
# -------------------------
_CHROMA_COLLECTION = None

def get_chroma_collection():
    global _CHROMA_COLLECTION
    if _CHROMA_COLLECTION is not None:
        return _CHROMA_COLLECTION

    api_key = os.getenv("CHROMA_API_KEY")
    tenant = os.getenv("CHROMA_TENANT")
    database = os.getenv("CHROMA_DATABASE")
    collection_name = os.getenv("CHROMA_COLLECTION", "richmond_policies")

    # Creating the client once saves significant network overhead
    client = chromadb.CloudClient(
        api_key=api_key,
        tenant=tenant,
        database=database
    )
    _CHROMA_COLLECTION = client.get_or_create_collection(name=collection_name)
    return _CHROMA_COLLECTION

# -------------------------
# 2) Retrieval Tool
# -------------------------
@tool
def search_richmond_policies(query: str):
    """
    Search the official University of Richmond policy manual. Use this tool whenever 
    you need to look up specific rules, procedures, requirements, or details 
    about university life (alcohol, drugs, health, etc.).
    """
    collection = get_chroma_collection()
    results = collection.query(
        query_texts=[query],
        n_results=15,
        include=["documents", "metadatas"],
    )

    if not results.get("documents") or not results["documents"][0]:
        return "No relevant context found in the policy manual."

    docs = []
    for text, meta in zip(results["documents"][0], results["metadatas"][0]):
        source = (meta or {}).get("source", "unknown")
        # Clean up source names
        clean_source = source.split("-")[1].replace("_", " ").title() if "-" in source else source
        docs.append(f"[SOURCE: {clean_source}]\n{text}")
    
    return "\n\n---\n\n".join(docs)

# -------------------------
# 3) Bedrock LLM
# -------------------------
def get_bedrock_llm():
    region = os.getenv("AWS_REGION")
    model_id = os.getenv("BEDROCK_MODEL_ID")

    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=region,
    )
    bedrock_client = session.client("bedrock-runtime")

    return ChatBedrock(
        model_id=model_id,
        client=bedrock_client,
        model_kwargs={"max_tokens": 1500, "temperature": 0.0},
    )

# -------------------------
# 4) DB-backed message history
# -------------------------
def get_history(session_id: str) -> SQLChatMessageHistory:
    db_url = os.getenv("DATABASE_URL", "sqlite:///./chat_memory.db")
    return SQLChatMessageHistory(
        session_id=session_id,
        connection_string=db_url,
        table_name="chat_messages",
    )

# -------------------------
# 5) Build chatbot agent
# -------------------------
def build_chatbot():
    llm = get_bedrock_llm()
    tools = [search_richmond_policies]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "You are the official Richmond Policy Assistant. Your primary tool is the policy search tool.\n\n"
             "Guidelines:\n"
             "1. Always search the policies if you are asked a factual question about Richmond.\n"
             "2. Provide actual rules, requirements, or procedures. Do not just summarize.\n"
             "3. If a user refers to a previous point (e.g., 'tell me more about #3'), look at the chat history to understand the context, then search for those specific details.\n"
             "4. Always cite the Source Name provided in the tool output.\n"
             "5. If you cannot find the info after searching, state that clearly."),
            ("placeholder", "{chat_history}"),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    
    executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True
    )

    with_memory = RunnableWithMessageHistory(
        executor,
        get_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    return with_memory
