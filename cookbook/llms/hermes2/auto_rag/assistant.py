from resources import vector_db  # type: ignore

from pas.assistant import Assistant
from pas.knowledge.embedder.ollama import OllamaEmbedder
from pas.knowledge import AssistantKnowledge
from pas.llm.ollama import Hermes
from pas.storage.assistant.postgres import PgAssistantStorage
from pas.knowledge.vectordb import PgVector2

knowledge_base = AssistantKnowledge(
    vector_db=PgVector2(
        db_url=vector_db.get_db_connection_local(),
        # Store embeddings in table: ai.hermes2_auto_rag_documents
        collection="hermes2_auto_rag_documents",
        # Use the OllamaEmbedder to generate embeddings
        embedder=OllamaEmbedder(
            model="adrienbrault/nous-hermes2pro:Q8_0", dimensions=4096
        ),
    ),
    # 3 references are added to the prompt
    num_documents=3,
)

storage = PgAssistantStorage(
    db_url=vector_db.get_db_connection_local(),
    # Store assistant runs in table: ai.hermes2_auto_rag
    table_name="hermes2_auto_rag",
)


def get_hermes_assistant(
    user_id: str | None = None,
    run_id: str | None = None,
    web_search: bool = False,
    debug_mode: bool = False,
) -> Assistant:
    """Get an Autonomous Hermes 2 Assistant."""

    introduction = "Hi, I'm an Autonomous RAG Assistant that uses function calling to answer questions.\n\n"
    introduction += "Upload a PDF and ask me questions."
    instructions = [
        f"You are interacting with the user: {user_id}",
        "When the user asks a question, search your knowledge base using the `search_knowledge_base` tool and provide a concise and relevant answer.",
        "Keep your conversation light hearted and fun.",
    ]

    return Assistant(
        name="hermes2_auto_rag_assistant",
        run_id=run_id,
        user_id=user_id,
        llm=Hermes(model="adrienbrault/nous-hermes2pro:Q8_0"),
        storage=storage,
        knowledge_base=knowledge_base,
        # Assistant introduction
        introduction=introduction,
        # Assistant instructions
        instructions=instructions,
        # This setting tells the LLM to format messages in markdown
        markdown=True,
        # use_tools adds default tools to search the knowledge base and chat history
        use_tools=True,
        # tools=assistant_tools,
        show_tool_calls=True,
        # Disable the read_chat_history tool to save tokens
        read_chat_history_tool=False,
        debug_mode=debug_mode,
    )
