from collections.abc import Iterator
from pathlib import Path

from pas.knowledge.base import AssistantKnowledge
from pas.knowledge.document import Document
from pas.knowledge.document.docx import DocxReader


class DocxKnowledgeBase(AssistantKnowledge):
    path: str | Path
    formats: list[str] = [".doc", ".docx"]
    reader: DocxReader = DocxReader()

    @property
    def document_lists(self) -> Iterator[list[Document]]:
        """Iterate over doc/docx files and yield lists of documents.
        Each object yielded by the iterator is a list of documents.

        Returns:
            Iterator[List[Document]]: Iterator yielding list of documents
        """

        _file_path: Path = Path(self.path) if isinstance(self.path, str) else self.path

        if _file_path.exists() and _file_path.is_dir():
            for _file in _file_path.glob("**/*"):
                if _file.suffix in self.formats:
                    yield self.reader.read(path=_file)
        elif (
            _file_path.exists()
            and _file_path.is_file()
            and _file_path.suffix in self.formats
        ):
            yield self.reader.read(path=_file_path)
