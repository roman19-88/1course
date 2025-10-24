import json

from src.services import (
    analyze_cashback_categories,
    investment_bank,
    search_person_transfers,
    search_phone_numbers,
    simple_search,
)

sample_transactions = [
    {"Дата операции": "2025-04-15", "Сумма операции": -100, "Категория": "Рестораны", "Описание": "KFC"},
    {"Дата операции": "2025-04-20", "Сумма операции": -200, "Категория": "Супермаркеты", "Описание": "Пятерочка"},
    {"Дата операции": "2025-04-25", "Сумма операции": 300, "Категория": "Зарплата", "Описание": ""},
    {"Дата операции": "2025-04-10", "Сумма операции": -50, "Категория": "Переводы", "Описание": "Валерий А."},
    {"Дата операции": "2025-04-12", "Сумма операции": -70, "Категория": "Переводы", "Описание": "Сергей З."},
    {"Дата операции": "2025-04-05", "Сумма операции": -30, "Категория": "Транспорт", "Описание": "Я МТС +7 921 11-22-33"},
    {"Дата операции": "2025-04-05", "Сумма операции": -40, "Категория": "Прочее", "Описание": "Оплата услуг"},
]

investment_transactions = [
    {"Дата операции": "2025-04-10", "Сумма операции": -1712},
    {"Дата операции": "2025-04-15", "Сумма операции": -50},
    {"Дата операции": "2025-04-20", "Сумма операции": -199},
    {"Дата операции": "2025-04-22", "Сумма операции": 300},
]


def test_analyze_cashback_categories():
    """Анализирует категории кэшбэка за указанный год и месяц"""
    json_result = analyze_cashback_categories(sample_transactions, 2025, 4)
    result = json.loads(json_result)
    assert "Рестораны" in result
    assert int(result["Рестораны"]) == 1


def test_investment_bank():
    """Рассчитывает сумму, которую можно отложить в копилку"""
    savings = investment_bank("2025-04", investment_transactions, 50)
    assert abs(savings - 39) < 1e-6


def test_simple_search():
    """Ищет транзакции, содержащие запрос в описании или категории"""
    result_json = simple_search("пятерочка", sample_transactions)
    result = json.loads(result_json)
    assert any("Пятерочка" in tx["Описание"] for tx in result)


def test_search_phone_numbers():
    """Возвращает транзакции, в описании которых есть российские номера"""
    result_json = search_phone_numbers(sample_transactions)
    result = json.loads(result_json)
    assert any("+7" in tx["Описание"] for tx in result)


def test_search_person_transfers():
    """Возвращает транзакции с категорией 'Переводы' и описанием"""
    result_json = search_person_transfers(sample_transactions)
    result = json.loads(result_json)
    assert all(tx["Категория"] == "Переводы" for tx in result)
    assert any("Валерий А." in tx["Описание"] or "Сергей З." in tx["Описание"] for tx in result)
