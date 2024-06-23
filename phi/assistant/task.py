import json
from collections.abc import Iterator
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from phi.assistant import Assistant


class Task(BaseModel):
    # -*- Task settings
    # Task name
    name: str | None = None
    # Task UUID (autogenerated if not set)
    task_id: str | None = Field(None, validate_default=True)
    # Task description
    description: str | None = None

    # Assistant to run this task
    assistant: Assistant | None = None
    # Reviewer for this task. Set reviewer=True for a default reviewer
    reviewer: Assistant | bool | None = None

    # -*- Task Output
    # Final output of this Task
    output: Any | None = None
    # If True, shows the output of the task in the workflow.run() function
    show_output: bool = True
    # Save the output to a file
    save_output_to_file: str | None = None

    # Cached values: do not set these directly
    _assistant: Assistant | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("task_id", mode="before")
    def set_task_id(cls, v: str | None) -> str:
        return v if v is not None else str(uuid4())

    @property
    def streamable(self) -> bool:
        return self.get_assistant().streamable

    def get_task_output_as_str(self) -> str | None:
        if self.output is None:
            return None

        if isinstance(self.output, str):
            return self.output

        if issubclass(self.output.__class__, BaseModel):
            # Convert current_task_message to json if it is a BaseModel
            return self.output.model_dump_json(exclude_none=True, indent=2)

        try:
            return json.dumps(self.output, indent=2)
        except Exception:
            return str(self.output)
        finally:
            return None

    def get_assistant(self) -> Assistant:
        if self._assistant is None:
            self._assistant = self.assistant or Assistant()
        return self._assistant

    def _run(
        self,
        message: list | dict | str | None = None,
        *,
        stream: bool = True,
        **kwargs: Any,
    ) -> Iterator[str]:
        assistant = self.get_assistant()
        assistant.task = self.description

        assistant_output = ""
        if stream and self.streamable:
            for chunk in assistant.run(message=message, stream=True, **kwargs):
                assistant_output += chunk if isinstance(chunk, str) else ""
                if self.show_output:
                    yield chunk if isinstance(chunk, str) else ""
        else:
            assistant_output = assistant.run(message=message, stream=False, **kwargs)  # type: ignore

        self.output = assistant_output
        if self.save_output_to_file:
            fn = self.save_output_to_file.format(name=self.name, task_id=self.task_id)
            with open(fn, "w") as f:
                f.write(self.output)

        # -*- Yield task output if not streaming
        if not stream:
            if self.show_output:
                yield self.output
            else:
                yield ""

    def run(
        self,
        message: list | dict | str | None = None,
        *,
        stream: bool = True,
        **kwargs: Any,
    ) -> Iterator[str] | str | BaseModel:
        if stream and self.streamable:
            resp = self._run(message=message, stream=True, **kwargs)
            return resp
        else:
            resp = self._run(message=message, stream=False, **kwargs)
            return next(resp)
