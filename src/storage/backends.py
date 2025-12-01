import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List


class StorageBackend(ABC):
    @abstractmethod
    async def write_file(self, path: str, content: str) -> str:
        """Write a file and return its public URL or path"""
        pass

    @abstractmethod
    async def read_file(self, path: str) -> str:
        """Read file content"""
        pass

    @abstractmethod
    async def list_files(self, prefix: str) -> List[Dict[str, str]]:
        """List files under prefix"""
        pass


# Local filesystem implementation (for development)
class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def write_file(self, path: str, content: str) -> str:
        full_path = self.base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return str(full_path)

    async def read_file(self, path: str) -> str:
        return (self.base_path / path).read_text()

    async def list_files(self, prefix: str) -> List[Dict[str, str]]:
        prefix_path = self.base_path / prefix
        files = []
        for p in prefix_path.rglob("*"):
            if p.is_file():
                files.append({
                    "path": str(p.relative_to(self.base_path)),
                    "type": "file"
                })
        return files


# HuggingFace Spaces implementation
class HuggingFaceStorageBackend(StorageBackend):
    def __init__(self):
        self.base_path = Path("/data")  # HF Spaces persistent storage
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def write_file(self, path: str, content: str) -> str:
        full_path = self.base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return str(full_path)

    async def read_file(self, path: str) -> str:
        return (self.base_path / path).read_text()

    async def list_files(self, prefix: str) -> List[Dict[str, str]]:
        prefix_path = self.base_path / prefix
        files = []
        for p in prefix_path.rglob("*"):
            if p.is_file():
                files.append({
                    "path": str(p.relative_to(self.base_path)),
                    "type": "file"
                })
        return files


# Initialize storage backend based on environment
storage_backend = (HuggingFaceStorageBackend()
                   if os.getenv("HUGGINGFACE_SPACE_ID")
                   else LocalStorageBackend("./output"))
