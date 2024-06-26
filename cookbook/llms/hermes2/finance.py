from pas.assistant import Assistant
from pas.llm.ollama import Hermes
from pas.tools.yfinance import YFinanceTools

assistant = Assistant(
    llm=Hermes(model="adrienbrault/nous-hermes2pro:Q8_0"),
    tools=[
        YFinanceTools(
            stock_price=True, analyst_recommendations=True, stock_fundamentals=True
        )
    ],
    show_tool_calls=True,
)
assistant.print_response(
    "Share the NVDA stock price and analyst recommendations", markdown=True
)
assistant.print_response("Summarize fundamentals for TSLA", markdown=True)
