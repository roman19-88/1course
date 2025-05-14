import datetime

import pandas as pd
import pytest

from src.views import (
    generate_events_page_response,
    generate_main_page_response,
    get_card_info,
    get_expenses_income_data,
    get_top_transactions,
)


@pytest.fixture
def sample_transactions_df():
    """Создаёт тестовый DataFrame с транзакциями для использования в тестах"""
    return pd.DataFrame({
        "date": [
            datetime.datetime(2025, 4, 5),
            datetime.datetime(2025, 4, 10),
            datetime.datetime(2025, 4, 15),
            datetime.datetime(2025, 3, 25),
        ],
        "card_number": [
            "1234567890123456",
            "1234567890123456",
            "9876543210987654",
            "9876543210987654",
        ],
        "amount": [100.0, -50.0, 200.0, -75.0],
        "category": ["Супермаркеты", "Рестораны", "Транспорт", "Переводы"],
        "description": ["Магнит", "KFC", "Такси", "Перевод денег"],
    })


def test_get_card_info(sample_transactions_df):
    """Проверяет корректность работы функции получения информации о картах"""
    cards_info = get_card_info(sample_transactions_df)
    assert len(cards_info) == 2
    for card in cards_info:
        assert "last_digits" in card
        assert "total_spent" in card
        assert "cashback" in card
        assert isinstance(card["last_digits"], str)
        assert isinstance(card["total_spent"], float)
        assert isinstance(card["cashback"], float)


def test_get_top_transactions(sample_transactions_df):
    """Проверяет функцию получения топ транзакций по сумме платежа"""
    top_txns = get_top_transactions(sample_transactions_df, limit=2)
    assert len(top_txns) == 2
    for txn in top_txns:
        assert "date" in txn
        assert "amount" in txn
        assert "category" in txn
        assert "description" in txn


def test_get_expenses_income_data(sample_transactions_df):
    """Проверяет анализ расходов и доходов по транзакциям"""
    expenses, income = get_expenses_income_data(sample_transactions_df)
    assert "total_amount" in expenses
    assert "main" in expenses
    assert "transfers_and_cash" in expenses
    assert "total_amount" in income
    assert "main" in income
    assert isinstance(expenses["main"], list)
    assert isinstance(expenses["transfers_and_cash"], list)
    assert isinstance(income["main"], list)


@pytest.fixture
def setup_test_data():
    """Фикстура для пути к файлу с транзакциями"""
    return "data/operations.xlsx"


def test_main_page_response(setup_test_data):
    """Проверяет корректность данных ответа главной страницы"""
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = generate_main_page_response(date_str)
    assert "greeting" in response
    assert "cards" in response
    assert "top_transactions" in response
    assert "currency_rates" in response
    assert "stock_prices" in response
    assert isinstance(response["greeting"], str)
    assert isinstance(response["cards"], list)
    assert isinstance(response["top_transactions"], list)
    assert isinstance(response["currency_rates"], list)
    assert isinstance(response["stock_prices"], list)
    assert response["greeting"] in [
        "Доброе утро",
        "Добрый день",
        "Добрый вечер",
        "Доброй ночи",
    ]


def test_events_page_response(setup_test_data):
    """Проверяет корректность данных ответа страницы событий для разных периодов"""
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for period in ["W", "M", "Y", "ALL"]:
        response = generate_events_page_response(date_str, period)
        assert "expenses" in response
        assert "income" in response
        assert "currency_rates" in response
        assert "stock_prices" in response
        expenses = response["expenses"]
        assert "total_amount" in expenses
        assert "main" in expenses
        assert "transfers_and_cash" in expenses
        assert isinstance(expenses["main"], list)
        assert isinstance(expenses["transfers_and_cash"], list)
        income = response["income"]
        assert "total_amount" in income
        assert "main" in income
        assert isinstance(income["main"], list)
