import json

from src.services import (
    analyze_cashback_categories,
    investment_bank,
    search_person_transfers,
    search_phone_numbers,
    simple_search,
)

sample_transactions = [
    {"date": "2025-04-15", "amount": -100, "category": "Рестораны", "description": "KFC"},
    {"date": "2025-04-20", "amount": -200, "category": "Супермаркеты", "description": "Пятерочка"},
    {"date": "2025-04-25", "amount": 300, "category": "Зарплата", "description": ""},
    {"date": "2025-04-10", "amount": -50, "category": "Переводы", "description": "Валерий А."},
    {"date": "2025-04-12", "amount": -70, "category": "Переводы", "description": "Сергей З."},
    {"date": "2025-04-05", "amount": -30, "category": "Транспорт", "description": "Я МТС +7 921 11-22-33"},
    {"date": "2025-04-05", "amount": -40, "category": "Прочее", "description": "Оплата услуг"},
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
    assert any("Пятерочка" in tx["description"] for tx in result)


def test_search_phone_numbers():
    """Возвращает транзакции, в описании которых есть российские номера"""
    result_json = search_phone_numbers(sample_transactions)
    result = json.loads(result_json)
    assert any("+7" in tx["description"] for tx in result)


def test_search_person_transfers():
    """Возвращает транзакции с категорией 'Переводы' и описанием"""
    result_json = search_person_transfers(sample_transactions)
    result = json.loads(result_json)
    assert all(tx["category"] == "Переводы" for tx in result)
    assert any("Валерий А." in tx["description"] or "Сергей З." in tx["description"] for tx in result)
