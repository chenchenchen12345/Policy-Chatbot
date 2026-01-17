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
_CHROMA_CLIENT = None
_CHROMA_COLLECTION = None

def get_chroma_collection():
    global _CHROMA_CLIENT, _CHROMA_COLLECTION
    if _CHROMA_COLLECTION is not None:
        return _CHROMA_COLLECTION

    import time
    start = time.time()
    api_key = os.getenv("CHROMA_API_KEY")
    tenant = os.getenv("CHROMA_TENANT")
    database = os.getenv("CHROMA_DATABASE")
    collection_name = os.getenv("CHROMA_COLLECTION", "richmond_policies")

    if _CHROMA_CLIENT is None:
        _CHROMA_CLIENT = chromadb.CloudClient(
            api_key=api_key,
            tenant=tenant,
            database=database
        )
    
    _CHROMA_COLLECTION = _CHROMA_CLIENT.get_collection(name=collection_name)
    print(f"[TIMER] Chroma collection connected in {time.time() - start:.2f}s")
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
    import time
    start = time.time()
    print(f"[TOOL] Searching for: {query}")
    collection = get_chroma_collection()
    results = collection.query(
        query_texts=[query],
        n_results=7,
        include=["documents", "metadatas"],
    )
    print(f"[TIMER] Chroma query (7 results) took {time.time() - start:.2f}s")

    if not results.get("documents") or not results["documents"][0]:
        return "No relevant context found in the policy manual."

    docs = []
    seen_texts = set()
    for text, meta in zip(results["documents"][0], results["metadatas"][0]):
        if text in seen_texts:
            continue
        seen_texts.add(text)
        
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
             "You are the official Richmond Policy Assistant. Your role is to help students, staff, and faculty accurately understand official University of Richmond policies.\n\n"
             "Your primary tool is the policy search tool.\n\n"
             "Guidelines:\n"
             "1. If a user asks a factual or policy-related question about the University of Richmond, always search the policies before responding.\n"
             "2. Provide exact rules, requirements, deadlines, or procedures when available. Do not speculate or provide unofficial guidance.\n"
             "3. If a user refers to a previous response (e.g., 'tell me more about #3'), use the chat history to understand context, then search for the specific policy section.\n"
             "4. Always cite the Source Name exactly as provided by the policy search tool.\n"
             "5. If relevant policy information cannot be found, clearly state that and explain what information is missing.\n"
             "6. Use a clear, calm, and student-friendly tone. Avoid legal jargon unless it appears in the policy.\n"
             "7. If a question is ambiguous or missing details, ask a brief clarifying question before answering.\n"
             "8. CRITICAL: When using the search_richmond_policies tool, you MUST rewrite the query to be standalone. Do not search for 'it', 'that policy', or 'the previous topic'. usage: search_richmond_policies(query='plagiarism policy for group projects') instead of search_richmond_policies(query='does it apply to group projects').\n"
             "9. Format responses for readability:\n"
             "   - **Bold the most important information** (deadlines, eligibility criteria, restrictions, requirements).\n"
             "   - Use **bullet points or numbered lists** when outlining steps, rules, or multiple conditions.\n"
             "   - Keep paragraphs short and scannable.\n"
             "9. Do not reveal internal reasoning, tool calls, or scratchpad content."),
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
    
    # OUTPUT PARSER: Fixes the issue where ChatBedrock returns a list of blocks,
    # causing the memory saver to crash with AttributeError.
    def parse_agent_output(output_dict):
        raw = output_dict.get("output", "")
        if isinstance(raw, list):
            # Flatten Claude's list of blocks into a single string
            text_parts = [b.get("text", "") for b in raw if b.get("type") == "text"]
            output_dict["output"] = " ".join(text_parts)
        return output_dict

    from langchain_core.runnables import RunnableLambda
    chain_with_parser = executor | RunnableLambda(parse_agent_output)

    with_memory = RunnableWithMessageHistory(
        chain_with_parser,
        get_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="output",
    )
    return with_memory
