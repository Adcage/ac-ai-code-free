import logging
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from app.tools.file_tools import FileTools

logger = logging.getLogger("app.tools.langchain_tools")


class WriteFileInput(BaseModel):
    relative_path: str = Field(description="文件相对路径，例如 src/App.vue")
    content: str = Field(description="要写入的文件内容")


class ReadFileInput(BaseModel):
    relative_path: str = Field(description="文件相对路径")


class ReadDirInput(BaseModel):
    relative_path: str = Field(default=".", description="目录相对路径，默认为项目根目录")


class WriteFileTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "write_file"
    description: str = "将内容写入指定文件。如果文件不存在则创建，如果目录不存在则自动创建。"
    args_schema: Type[BaseModel] = WriteFileInput
    file_tools: FileTools | None = None

    def _run(self, relative_path: str, content: str) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(self, relative_path: str, content: str) -> str:
        return await self.file_tools.write_file(relative_path, content)


class ReadFileTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "read_file"
    description: str = "读取指定文件的内容。"
    args_schema: Type[BaseModel] = ReadFileInput
    file_tools: FileTools | None = None

    def _run(self, relative_path: str) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(self, relative_path: str) -> str:
        return await self.file_tools.read_file(relative_path)


class ReadDirTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "read_dir"
    description: str = "列出指定目录下的文件和子目录。"
    args_schema: Type[BaseModel] = ReadDirInput
    file_tools: FileTools | None = None

    def _run(self, relative_path: str = ".") -> str:
        raise NotImplementedError("Use async version")

    async def _arun(self, relative_path: str = ".") -> str:
        return await self.file_tools.read_dir(relative_path)


def create_file_tools(file_tools: FileTools) -> list[BaseTool]:
    return [
        WriteFileTool(file_tools=file_tools),
        ReadFileTool(file_tools=file_tools),
        ReadDirTool(file_tools=file_tools),
    ]
