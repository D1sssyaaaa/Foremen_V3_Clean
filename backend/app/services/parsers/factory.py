from typing import Dict, Type
from app.services.parsers.base import BaseParser
from app.upd.upd_parser import UPDParser, UPDDocument

class XmlUPDParserWrapper(BaseParser):
    """Обертка над существующим XML парсером"""
    def __init__(self):
        self._parser = UPDParser()

    def parse(self, content: bytes, filename: str = "") -> UPDDocument:
        # Используем существующий метод
        return self._parser.parse(content)

class ParserFactory:
    """Фабрика парсеров документов"""
    
    _parsers: Dict[str, Type[BaseParser]] = {
        "xml": XmlUPDParserWrapper,
        # "xlsx": ExcelParser,  # TODO: Implement Excel parser
        # "xls": ExcelParser,
        # "pdf": PdfParser,     # TODO: Implement PDF parser
    }

    @classmethod
    def get_parser(cls, filename: str) -> BaseParser:
        """Получить парсер по расширению файла"""
        extension = filename.split(".")[-1].lower() if "." in filename else ""
        
        parser_cls = cls._parsers.get(extension)
        if not parser_cls:
            # Fallback: XML (так как это основной формат УПД)
            # или можно выбрасывать ошибку
            if extension in ["xml", "upd"]:
                return XmlUPDParserWrapper()
            
            raise ValueError(f"Неподдерживаемый формат файла: .{extension}")

        return parser_cls()
