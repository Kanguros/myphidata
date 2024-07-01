import json
from collections.abc import Callable, Iterator
from typing import Any

from pydantic import BaseModel, ConfigDict

from pas.tools import Tool, Toolkit
from pas.tools.function import Function, FunctionCall
from pas.utils.log import logger
from pas.utils.timer import Timer


class InvalidToolCallException(Exception):
    pass


class Message(BaseModel):
    """Model for LLM messages"""

    # The role of the message author.
    # One of system, user, assistant, or function.
    role: str
    # The contents of the message. content is required for all messages,
    # and may be null for assistant messages with function calls.
    content: list[dict] | str | None = None
    # An optional name for the participant.
    # Provides the model information to differentiate between participants of the same role.
    name: str | None = None
    # Tool call that this message is responding to.
    tool_call_id: str | None = None
    # The name of the tool call
    tool_call_name: str | None = None
    # The tool calls generated by the model, such as function calls.
    tool_calls: list[dict[str, Any]] | None = None
    # Metrics for the message, tokes + the time it took to generate the response.
    metrics: dict[str, Any] = {}
    # Internal identifier for the message.
    internal_id: str | None = None

    # DEPRECATED: The name and arguments of a function that should be called, as generated by the model.
    function_call: dict[str, Any] | None = None

    model_config = ConfigDict(extra="allow")

    def get_content_string(self) -> str:
        """Returns the content as a string."""
        if isinstance(self.content, str):
            return self.content
        if isinstance(self.content, list):
            import json

            return json.dumps(self.content)
        return ""

    def to_dict(self) -> dict[str, Any]:
        _dict = self.model_dump(
            exclude_none=True,
            exclude={"metrics", "tool_call_name", "internal_id"},
        )
        # Manually add the content field if it is None
        if self.content is None:
            _dict["content"] = None
        return _dict

    def log(self, level: str | None = None):
        """Log the message to the console

        @param level: The level to log the message at. One of debug, info, warning, or error.
            Defaults to debug.
        """
        _logger = logger.debug
        if level == "debug":
            _logger = logger.debug
        elif level == "info":
            _logger = logger.info
        elif level == "warning":
            _logger = logger.warning
        elif level == "error":
            _logger = logger.error

        _logger(f"============== {self.role} ==============")
        if self.name:
            _logger(f"Name: {self.name}")
        if self.tool_call_id:
            _logger(f"Call Id: {self.tool_call_id}")
        if self.content:
            _logger(self.content)
        if self.tool_calls:
            _logger(f"Tool Calls: {json.dumps(self.tool_calls, indent=2)}")
        if self.function_call:
            _logger(f"Function Call: {json.dumps(self.function_call, indent=2)}")
        # if self.model_extra and "images" in self.model_extra:
        #     _logger("images: {}".format(self.model_extra["images"]))

    def content_is_valid(self) -> bool:
        """Check if the message content is valid."""

        return self.content is not None and len(self.content) > 0


class References(BaseModel):
    """Model for LLM references"""

    # The question asked by the user.
    query: str
    # The references from the vector database.
    references: str | None = None
    # Performance in seconds.
    time: float | None = None


class LLM(BaseModel):
    # ID of the model to use.
    model: str
    # Name for this LLM. Note: This is not sent to the LLM API.
    name: str | None = None
    # Metrics collected for this LLM. Note: This is not sent to the LLM API.
    metrics: dict[str, Any] = {}
    response_format: Any | None = None

    # A list of tools provided to the LLM.
    # Tools are functions the model may generate JSON inputs for.
    # If you provide a dict, it is not called by the model.
    # Always add tools using the add_tool() method.
    tools: list[Tool | dict] | None = None
    # Controls which (if any) function is called by the model.
    # "none" means the model will not call a function and instead generates a message.
    # "auto" means the model can pick between generating a message or calling a function.
    # Specifying a particular function via {"type: "function", "function": {"name": "my_function"}}
    #   forces the model to call that function.
    # "none" is the default when no functions are present. "auto" is the default if functions are present.
    tool_choice: str | dict[str, Any] | None = None
    # If True, runs the tool before sending back the response content.
    run_tools: bool = True
    # If True, shows function calls in the response.
    show_tool_calls: bool | None = None

    # -*- Functions available to the LLM to call -*-
    # Functions extracted from the tools.
    # Note: These are not sent to the LLM API and are only used for execution + deduplication.
    functions: dict[str, Function] | None = None
    # Maximum number of function calls allowed across all iterations.
    function_call_limit: int = 10
    # Function call stack.
    function_call_stack: list[FunctionCall] | None = None

    system_prompt: str | None = None
    instructions: list[str] | None = None

    # State from the run
    run_id: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def api_kwargs(self) -> dict[str, Any]:
        raise NotImplementedError

    def invoke(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    async def ainvoke(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    def invoke_stream(self, *args, **kwargs) -> Iterator[Any]:
        raise NotImplementedError

    async def ainvoke_stream(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    def response(self, messages: list[Message]) -> str:
        raise NotImplementedError

    async def aresponse(self, messages: list[Message]) -> str:
        raise NotImplementedError

    def response_stream(self, messages: list[Message]) -> Iterator[str]:
        raise NotImplementedError

    async def aresponse_stream(self, messages: list[Message]) -> Any:
        raise NotImplementedError

    def generate(self, messages: list[Message]) -> dict:
        raise NotImplementedError

    def generate_stream(self, messages: list[Message]) -> Iterator[dict]:
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        _dict = self.model_dump(include={"name", "model", "metrics"})
        if self.functions:
            _dict["functions"] = {k: v.to_dict() for k, v in self.functions.items()}
            _dict["function_call_limit"] = self.function_call_limit
        return _dict

    def get_tools_for_api(self) -> list[dict[str, Any]] | None:
        if self.tools is None:
            return None

        tools_for_api = []
        for tool in self.tools:
            if isinstance(tool, Tool):
                tools_for_api.append(tool.to_dict())
            elif isinstance(tool, dict):
                tools_for_api.append(tool)
        return tools_for_api

    def add_tool(self, tool: Tool | Toolkit | Callable | dict | Function) -> None:
        if self.tools is None:
            self.tools = []

        # If the tool is a Tool or Dict, add it directly to the LLM
        if isinstance(tool, (Tool, dict)):
            if tool not in self.tools:
                self.tools.append(tool)
                logger.debug(f"Added tool {tool} to LLM.")

        # If the tool is a Callable or Toolkit, add its functions to the LLM
        elif callable(tool) or isinstance(tool, (Toolkit, Function)):
            if self.functions is None:
                self.functions = {}

            if isinstance(tool, Toolkit):
                # For each function in the toolkit
                for name, func in tool.functions.items():
                    # If the function does not exist in self.functions, add to self.tools
                    if name not in self.functions:
                        self.functions[name] = func
                        self.tools.append(
                            {"type": "function", "function": func.to_dict()},
                        )
                        logger.debug(f"Function {name} from {tool.name} added to LLM.")

            elif isinstance(tool, Function):
                if tool.name not in self.functions:
                    self.functions[tool.name] = tool
                    self.tools.append({"type": "function", "function": tool.to_dict()})
                    logger.debug(f"Function {tool.name} added to LLM.")

            elif callable(tool):
                try:
                    function_name = tool.__name__
                    if function_name not in self.functions:
                        func = Function.from_callable(tool)
                        self.functions[func.name] = func
                        self.tools.append(
                            {"type": "function", "function": func.to_dict()},
                        )
                        logger.debug(f"Function {func.name} added to LLM.")
                except Exception as e:
                    logger.warning(f"Could not add function {tool}: {e}")

    def deactivate_function_calls(self) -> None:
        # Deactivate tool calls by setting future tool calls to "none"
        # This is triggered when the function call limit is reached.
        self.tool_choice = "none"

    def run_function_calls(
        self,
        function_calls: list[FunctionCall],
        role: str = "tool",
    ) -> list[Message]:
        function_call_results: list[Message] = []
        for function_call in function_calls:
            if self.function_call_stack is None:
                self.function_call_stack = []

            # -*- Run function call
            _function_call_timer = Timer()
            _function_call_timer.start()
            function_call.execute()
            _function_call_timer.stop()
            _function_call_result = Message(
                role=role,
                content=function_call.result,
                tool_call_id=function_call.call_id,
                tool_call_name=function_call.function.name,
                metrics={"time": _function_call_timer.elapsed},
            )
            if "tool_call_times" not in self.metrics:
                self.metrics["tool_call_times"] = {}
            if function_call.function.name not in self.metrics["tool_call_times"]:
                self.metrics["tool_call_times"][function_call.function.name] = []
            self.metrics["tool_call_times"][function_call.function.name].append(
                _function_call_timer.elapsed,
            )
            function_call_results.append(_function_call_result)
            self.function_call_stack.append(function_call)

            # -*- Check function call limit
            if len(self.function_call_stack) >= self.function_call_limit:
                self.deactivate_function_calls()
                break  # Exit early if we reach the function call limit

        return function_call_results

    def get_system_prompt_from_llm(self) -> str | None:
        return self.system_prompt

    def get_instructions_from_llm(self) -> list[str] | None:
        return self.instructions