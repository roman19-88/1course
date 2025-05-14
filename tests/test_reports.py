from datetime import datetime, timedelta
from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from src.reports import get_date_range, spending_by_category, spending_by_weekday, spending_by_workday


@pytest.fixture
def test_transactions():
    """Создает тестовый набор транзакций для использования в тестах"""
    base_date = datetime(2023, 5, 15)

    data = []
    for i in range(1, 80, 2):
        day = base_date - timedelta(days=i)
        if day.weekday() < 5:
            data.append({
                'date': day.strftime('%Y-%m-%d'),
                'amount': -100,
                'category': 'Рестораны',
                'description': 'Обед в рабочий день'
            })

    for i in range(2, 80, 2):
        day = base_date - timedelta(days=i)
        if day.weekday() >= 5:
            data.append({
                'date': day.strftime('%Y-%m-%d'),
                'amount': -200,
                'category': 'Развлечения',
                'description': 'Развлечения в выходной'
            })

    for i in range(5, 70, 10):
        day = base_date - timedelta(days=i)
        data.append({
            'date': day.strftime('%Y-%m-%d'),
            'amount': -150,
            'category': 'Транспорт',
            'description': 'Поездка на такси'
        })

    for i in range(10, 80, 30):
        day = base_date - timedelta(days=i)
        data.append({
            'date': day.strftime('%Y-%m-%d'),
            'amount': 1000,
            'category': 'Зарплата',
            'description': 'Ежемесячная зарплата'
        })

    return pd.DataFrame(data)


def test_get_date_range():
    """Тестирование функции получения диапазона дат"""
    start, end = get_date_range("2023-05-15")
    assert end == datetime(2023, 5, 15)
    assert start == datetime(2023, 2, 14)

    start, end = get_date_range()
    today = datetime.now()
    assert end.year == today.year
    assert end.month == today.month
    assert end.day == today.day
    assert (end - start).days == 90


def test_spending_by_category(test_transactions):
    """Тестирование отчета по категории"""
    with patch("builtins.open", mock_open()) as mock_file:
        result = spending_by_category(test_transactions, "Рестораны", "2023-05-15")

        assert mock_file.called
        assert isinstance(result, pd.DataFrame)
        assert all(result['total_spending'] > 0)


def test_spending_by_weekday(test_transactions):
    """Тестирует функционал отчета по средним тратам в разные дни недели"""
    with patch("builtins.open", mock_open()) as mock_file:
        result = spending_by_weekday(test_transactions, "2023-05-15")

        assert mock_file.called
        assert isinstance(result, pd.DataFrame)
        assert all(result['average_spending'] > 0)
        assert list(result['weekday']) == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def test_spending_by_workday(test_transactions):
    """Тестирует функционал отчета по средним тратам в рабочие/выходные дни"""
    with patch("builtins.open", mock_open()) as mock_file:
        result = spending_by_workday(test_transactions, "2023-05-15")

        assert mock_file.called
        assert isinstance(result, pd.DataFrame)
        assert set(result['day_type']) == {'workday', 'weekend'}
        assert all(result['average_spending'] > 0)

        weekend_spending = result[result['day_type'] == 'weekend']['average_spending'].values[0]
        workday_spending = result[result['day_type'] == 'workday']['average_spending'].values[0]

        assert weekend_spending > workday_spending
