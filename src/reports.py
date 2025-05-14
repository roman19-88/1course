import functools
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def save_report(filename=None):
    """Декоратор для сохранения результатов отчетов в файл"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            default_filename = f"{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_file = filename or default_filename

            os.makedirs("reports", exist_ok=True)
            output_path = os.path.join("reports", output_file)

            try:
                if isinstance(result, pd.DataFrame):
                    result_dict = result.to_dict(orient="records")
                else:
                    result_dict = result

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result_dict, f, ensure_ascii=False, indent=2)

                logger.info(f"Отчет успешно сохранен в файл: {output_path}")
            except Exception as e:
                logger.error(f"Ошибка при сохранении отчета: {e}")

            return result

        return wrapper

    if callable(filename):
        func = filename
        filename = None
        return decorator(func)

    return decorator


def get_date_range(date: Optional[str] = None) -> tuple[datetime, datetime]:
    """Получает диапазон дат для отчета: от текущей/указанной даты на 3 месяца назад"""
    if date:
        end_date = datetime.strptime(date, "%Y-%m-%d")
    else:
        end_date = datetime.now()

    start_date = end_date - timedelta(days=90)
    return start_date, end_date


@save_report
def spending_by_category(transactions: pd.DataFrame,
                         category: str,
                         date: Optional[str] = None) -> pd.DataFrame:
    """Возвращает траты по заданной категории за последние 3 месяца"""
    try:
        start_date, end_date = get_date_range(date)

        filtered = transactions[
            (pd.to_datetime(transactions['date']) >= start_date)
            & (pd.to_datetime(transactions['date']) <= end_date)
            & (transactions['category'] == category)
            & (transactions['amount'] < 0)
        ]


        result = filtered.groupby(pd.to_datetime(filtered['date']).dt.date).agg({
            'amount': 'sum',
            'category': 'count'
        }).reset_index()

        result = result.rename(columns={
            'date': 'date',
            'amount': 'total_spending',
            'category': 'transactions_count'
        })

        result['total_spending'] = result['total_spending'].abs()

        logger.info(f"Отчет по категории '{category}' сформирован успешно: найдено {len(result)} записей")
        return result

    except Exception as e:
        logger.error(f"Ошибка при формировании отчета по категории '{category}': {e}")
        return pd.DataFrame()


@save_report("weekday_spending.json")
def spending_by_weekday(transactions: pd.DataFrame,
                        date: Optional[str] = None) -> pd.DataFrame:
    """Возвращает средние траты в каждый из дней недели за последние 3 месяца"""
    try:
        start_date, end_date = get_date_range(date)

        filtered = transactions[
            (pd.to_datetime(transactions['date']) >= start_date)
            & (pd.to_datetime(transactions['date']) <= end_date)
            & (transactions['amount'] < 0)
        ].copy()

        filtered['weekday'] = pd.to_datetime(filtered['date']).dt.day_name()

        result = filtered.groupby('weekday').agg({
            'amount': lambda x: abs(x.mean())
        }).reset_index()

        result = result.rename(columns={
            'amount': 'average_spending'
        })

        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        result['weekday_order'] = result['weekday'].map(lambda x: weekday_order.index(x))
        result = result.sort_values('weekday_order').drop('weekday_order', axis=1)

        logger.info("Отчет по дням недели сформирован успешно")
        return result

    except Exception as e:
        logger.error(f"Ошибка при формировании отчета по дням недели: {e}")
        return pd.DataFrame()


@save_report
def spending_by_workday(transactions: pd.DataFrame,
                        date: Optional[str] = None) -> pd.DataFrame:
    """Возвращает средние траты в рабочий и выходной день за последние 3 месяца"""
    try:
        start_date, end_date = get_date_range(date)

        filtered = transactions[
            (pd.to_datetime(transactions['date']) >= start_date)
            & (pd.to_datetime(transactions['date']) <= end_date)
            & (transactions['amount'] < 0)
        ].copy()

        filtered['is_weekend'] = pd.to_datetime(filtered['date']).dt.dayofweek.isin(
            [5, 6])
        filtered['day_type'] = filtered['is_weekend'].map({True: 'weekend', False: 'workday'})

        result = filtered.groupby('day_type').agg({
            'amount': lambda x: abs(x.mean())
        }).reset_index()

        result = result.rename(columns={
            'amount': 'average_spending'
        })

        logger.info("Отчет по типам дней сформирован успешно")
        return result

    except Exception as e:
        logger.error(f"Ошибка при формировании отчета по типам дней: {e}")
        return pd.DataFrame()
