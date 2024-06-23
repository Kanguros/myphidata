from pas.assistant import Assistant
from pas.llm.anthropic import Claude
from pas.tools.exa import ExaTools
from pas.tools.website import WebsiteTools

assistant = Assistant(
    llm=Claude(), tools=[ExaTools(), WebsiteTools()], show_tool_calls=True
)
assistant.print_response(
    "Produce this table: research chromatic homotopy theory."
    "Access each link in the result outputting the summary for that article, its link, and keywords; "
    "After the table output make conceptual ascii art of the overarching themes and constructions",
    markdown=True,
)
