from abc import ABC, abstractmethod
from typing import BinaryIO, Union
from app.upd.upd_parser import UPDDocument

class BaseParser(ABC):
    """Базовый интерфейс для всех парсеров документов (XML, Excel, PDF)"""
    
    @abstractmethod
    def parse(self, content: bytes, filename: str = "") -> UPDDocument:
        """
        Парсинг содержимого файла.
        Должен вернуть унифицированный UPDDocument.
        """
        pass
