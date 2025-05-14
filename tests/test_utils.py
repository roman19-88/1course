import datetime
import os
import time
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.utils import (
    filter_transactions_by_month,
    filter_transactions_by_period,
    get_currency_rates,
    get_greeting,
    get_stock_prices,
    load_user_settings,
    with_cache,
)


def test_with_cache_caches_result():
    """Функция кеширует результат"""
    mock_func = MagicMock(return_value="result")

    result1 = with_cache(mock_func, "key", ttl=2)
    assert result1 == "result"
    assert mock_func.call_count == 1

    result2 = with_cache(mock_func, "key", ttl=2)
    assert result2 == "result"
    assert mock_func.call_count == 1

    time.sleep(2)

    result3 = with_cache(mock_func, "key", ttl=2)
    assert result3 == "result"
    assert mock_func.call_count == 2


@pytest.fixture
def sample_transactions_df():
    """Создает тестовый DataFrame с транзакциями."""
    return pd.DataFrame(
        {
            "date": [
                datetime.datetime(2025, 4, 5),
                datetime.datetime(2025, 4, 10),
                datetime.datetime(2025, 4, 15),
                datetime.datetime(2025, 3, 25),  # Предыдущий месяц
            ],
            "card_number": [
                "1234567890123456",
                "9876543210987654",
                "1234567890123456",
                "9876543210987654",
            ],
            "amount": [100.0, -50.0, 200.0, -75.0],
            "category": ["Супермаркеты", "Рестораны", "Транспорт", "Развлечения"],
            "description": ["Магнит", "KFC", "Такси", "Кино"],
        }
    )


def test_filter_transactions_by_month(sample_transactions_df):
    """Тест фильтрации транзакций по месяцу."""
    date_str = "2025-04-15 12:00:00"
    filtered_df = filter_transactions_by_month(sample_transactions_df, date_str)

    assert len(filtered_df) == 3
    assert all(date.month == 4 for date in filtered_df["date"])
    assert not any(date.month == 3 for date in filtered_df["date"])


def test_filter_transactions_by_period(sample_transactions_df):
    """Тест фильтрации транзакций по разным периодам."""
    date_str = "2025-04-15 12:00:00"

    month_df = filter_transactions_by_period(sample_transactions_df, date_str, "M")
    assert len(month_df) == 3

    year_df = filter_transactions_by_period(sample_transactions_df, date_str, "Y")
    assert len(year_df) == 4

    custom_df = filter_transactions_by_period(sample_transactions_df, date_str, "CUSTOM")
    assert len(custom_df) == 3


def test_get_greeting():
    """Тестирует определение приветствия в зависимости от времени."""
    assert get_greeting("2025-04-15 08:00:00") == "Доброе утро"
    assert get_greeting("2025-04-15 14:00:00") == "Добрый день"
    assert get_greeting("2025-04-15 20:00:00") == "Добрый вечер"
    assert get_greeting("2025-04-15 02:00:00") == "Доброй ночи"


@patch("builtins.open")
def test_load_user_settings(mock_open):
    """Тест загрузки пользовательских настроек."""
    mock_open.return_value.__enter__.return_value.read.return_value = (
        '{"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "MSFT"]}'
    )

    settings = load_user_settings()

    assert "user_currencies" in settings
    assert "user_stocks" in settings
    assert settings["user_currencies"] == ["USD", "EUR"]
    assert settings["user_stocks"] == ["AAPL", "MSFT"]


@patch("src.utils.requests.get")
@patch("src.utils.with_cache")
def test_get_currency_rates_with_api_key(mock_with_cache, mock_get):
    os.environ["EXCHANGE_API_KEY"] = "test_api_key"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"rates": {"USD": 0.012, "EUR": 0.01}}
    mock_get.return_value = mock_response

    def fetch_data():
        headers = {}
        api_key = os.getenv("EXCHANGE_API_KEY", "")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        mock_get("https://open.er-api.com/v6/latest/RUB", headers=headers)
        return {"rates": {"USD": 0.012, "EUR": 0.01}}

    mock_with_cache.side_effect = lambda func, key, ttl=3600: fetch_data()

    currencies = ["USD", "EUR"]
    rates = get_currency_rates(currencies)

    mock_get.assert_called_once()
    called_headers = mock_get.call_args.kwargs.get("headers", {})
    assert called_headers.get("Authorization") == "Bearer test_api_key"

    assert len(rates) == 2
    assert rates[0]["currency"] == "USD"
    assert rates[1]["currency"] == "EUR"

    del os.environ["EXCHANGE_API_KEY"]


@patch("src.utils.requests.get")
@patch("src.utils.with_cache")
def test_get_currency_rates_no_api_key(mock_with_cache, mock_get):
    os.environ.pop("EXCHANGE_API_KEY", None)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"rates": {"USD": 0.012, "EUR": 0.01}}
    mock_get.return_value = mock_response

    def fetch_data():
        mock_get("https://open.er-api.com/v6/latest/RUB")
        return {"rates": {"USD": 0.012, "EUR": 0.01}}

    mock_with_cache.side_effect = lambda func, key, ttl=3600: fetch_data()

    currencies = ["USD", "EUR"]
    rates = get_currency_rates(currencies)

    mock_get.assert_called_once()
    called_headers = mock_get.call_args.kwargs.get("headers", {})
    assert "Authorization" not in called_headers

    assert len(rates) == 2


@patch("src.utils.with_cache")
def test_get_stock_prices(mock_with_cache):
    """Тест получения цены акций."""
    mock_with_cache.return_value = 150.75

    stocks = ["AAPL", "MSFT"]
    prices = get_stock_prices(stocks)

    assert len(prices) == 2
    assert prices[0]["stock"] == "AAPL"
    assert prices[1]["stock"] == "MSFT"
    assert prices[0]["price"] == 150.75
