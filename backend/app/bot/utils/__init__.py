"""Утилиты бота"""

__all__ = ["APIClient", "format_date", "format_money"]

from .api_client import APIClient
from datetime import date, datetime
from decimal import Decimal


def format_date(d: date | datetime | str) -> str:
    """Форматирование даты в читаемый вид"""
    if isinstance(d, str):
        try:
            d = datetime.fromisoformat(d.replace('Z', '+00:00')).date()
        except:
            return d
    
    if isinstance(d, datetime):
        d = d.date()
    
    return d.strftime("%d.%m.%Y")


def format_money(amount: Decimal | float | int) -> str:
    """Форматирование суммы"""
    return f"{amount:,.2f} ₽".replace(",", " ")


def escape_markdown(text: str) -> str:
    """Экранирование спецсимволов Markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text
