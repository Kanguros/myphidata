from pas.assistant import Assistant
from pas.llm.openai.like import OpenAILike

assistant = Assistant(llm=OpenAILike(base_url="http://localhost:1234/v1"))
assistant.cli_app(markdown=True)
