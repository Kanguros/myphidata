"""
This cookbook shows how to use a custom function to generate references for RAG.

You can use the custom_references_function to generate references for the RAG model.
The function takes a query and returns a list of references from the knowledge base.
"""

import json

from pas.assistant import Assistant
from pas.knowledge.document import Document
from pas.knowledge.pdf import PDFUrlKnowledgeBase
from pas.knowledge.vectordb import PgVector2

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://phi-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=PgVector2(collection="recipes", db_url=db_url),
)
# Comment out after first run
# knowledge_base.load(recreate=False)


def custom_references_function(query: str, **kwargs) -> str | None:
    """Return a list of references from the knowledge base"""
    print(f"-*- Searching for references for query: {query}")
    relevant_docs: list[Document] = knowledge_base.search(query=query, num_documents=5)
    if len(relevant_docs) == 0:
        return None

    return json.dumps([doc.to_dict() for doc in relevant_docs], indent=2)


assistant = Assistant(
    knowledge_base=knowledge_base,
    # Generate references using a custom function.
    references_function=custom_references_function,
    # Adds references to the prompt.
    add_references_to_prompt=True,
)
assistant.print_response("How to make Thai curry?", markdown=True)
