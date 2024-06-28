import typer
from resources import vector_db  # type: ignore
from rich.prompt import Prompt

from pas.assistant import Assistant
from pas.knowledge.pdf import PDFUrlKnowledgeBase
from pas.storage.assistant.postgres import PgAssistantStorage
from pas.knowledge.vectordb import PgVector2

knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://phi-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=PgVector2(
        collection="recipes", db_url=vector_db.get_db_connection_local()
    ),
)
# Comment out after first run
knowledge_base.load(recreate=False)

storage = PgAssistantStorage(
    table_name="pdf_assistant", db_url=vector_db.get_db_connection_local()
)


def pdf_assistant(new: bool = False, user: str = "user"):
    run_id: str | None = None

    if not new:
        existing_run_ids: list[str] = storage.get_all_run_ids(user)
        if len(existing_run_ids) > 0:
            run_id = existing_run_ids[0]

    assistant = Assistant(
        run_id=run_id,
        user_id=user,
        knowledge_base=knowledge_base,
        storage=storage,
        # tool_calls=True adds functions to
        # search the knowledge base and chat history
        use_tools=True,
        show_tool_calls=True,
        # Uncomment the following line to use traditional RAG
        # add_references_to_prompt=True,
    )
    if run_id is None:
        run_id = assistant.run_id
        print(f"Started Run: {run_id}\n")
    else:
        print(f"Continuing Run: {run_id}\n")

    while True:
        message = Prompt.ask(f"[bold] :sunglasses: {user} [/bold]")
        if message in ("exit", "bye"):
            break
        assistant.print_response(message, markdown=True)


if __name__ == "__main__":
    typer.run(pdf_assistant)
