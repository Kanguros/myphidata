# Please install dependencies using: pip install -U ollama phidata openai
from pas.assistant import Assistant
from pas.llm.ollama.openai import OllamaOpenAI

assistant = Assistant(
    llm=OllamaOpenAI(model="tinyllama"),
    system_prompt="Who are you and who created you? Respond in 1 sentence.",
)
assistant.print_response(markdown=True)
