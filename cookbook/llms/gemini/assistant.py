from os import getenv

import vertexai

from pas.assistant import Assistant
from pas.llm.gemini import Gemini

# *********** Initialize VertexAI ***********
vertexai.init(project=getenv("PROJECT_ID"), location=getenv("LOCATION"))

assistant = Assistant(
    llm=Gemini(model="gemini-1.5-pro-preview-0409"),
    description="You help people with their health and fitness goals.",
)
assistant.print_response("Share a quick healthy breakfast recipe.", markdown=True)
