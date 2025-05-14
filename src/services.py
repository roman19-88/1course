import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def analyze_cashback_categories(
    data: List[Dict[str, Any]], year: int, month: int
) -> str:
    """Анализирует категории кешбэка за указанный год и месяц"""

    try:
        filtered = filter(
            lambda tx: (
                "date" in tx
                and "amount" in tx
                and "category" in tx
                and datetime.strptime(tx["date"], "%Y-%m-%d").year == year
                and datetime.strptime(tx["date"], "%Y-%m-%d").month == month
                and tx["amount"] < 0
            ),
            data,
        )

        cashback_totals = {}
        for tx in filtered:
            category = tx["category"]
            cashback_amount = abs(tx["amount"]) * 0.01
            cashback_totals[category] = cashback_totals.get(category, 0) + cashback_amount

        cashback_totals_rounded = {k: int(round(v)) for k, v in cashback_totals.items()}

        result_json = json.dumps(cashback_totals_rounded, ensure_ascii=False)
        logger.info(f"Произведён анализ кешбэка: {result_json}")
        return result_json

    except Exception as e:
        logger.error(f"Ошибка анализа кешбэка: {e}")
        return json.dumps({})


def investment_bank(
    month: str, transactions: List[Dict[str, Any]], limit: int
) -> float:
    """Рассчитывает сумму, которую можно отложить в инвесткопилку за указанный месяц"""

    try:

        def round_sum(amount: float) -> float:
            rounded = ((int(amount) + limit - 1) // limit) * limit
            return rounded

        filtered = filter(
            lambda tx: tx["Дата операции"].startswith(month) and tx["Сумма операции"] < 0,
            transactions,
        )

        savings = sum(
            round_sum(abs(tx["Сумма операции"])) - abs(tx["Сумма операции"])
            for tx in filtered
        )

        logger.info(f"В инвесткопилку за {month} можно отложить: {savings}")
        return savings

    except Exception as e:
        logger.error(f"Ошибка расчета инвесткопилки: {e}")
        return 0.0


def simple_search(query: str, transactions: List[Dict[str, Any]]) -> str:
    """Ищет транзакции, содержащие query в описании или категории"""

    try:
        lower_query = query.lower()
        filtered = filter(
            lambda tx: (
                ("description" in tx and lower_query in tx["description"].lower())
                or ("category" in tx and lower_query in tx["category"].lower())
            ),
            transactions,
        )

        result = list(filtered)
        json_result = json.dumps(result, ensure_ascii=False)
        logger.info(f"Простой поиск '{query}': найдено {len(result)} транзакций")
        return json_result

    except Exception as e:
        logger.error(f"Ошибка в простом поиске: {e}")
        return json.dumps([])


PHONE_PATTERN = re.compile(r"\+7\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{2}")


def search_phone_numbers(transactions: List[Dict[str, Any]]) -> str:
    """Возвращает JSON с транзакциями, в описаниях которых есть российские номера мобильных"""

    try:
        filtered = filter(
            lambda tx: "description" in tx and PHONE_PATTERN.search(tx["description"]),
            transactions,
        )

        result = list(filtered)
        json_result = json.dumps(result, ensure_ascii=False)
        logger.info(f"Поиск телефонных номеров: найдено {len(result)} транзакций")
        return json_result

    except Exception as e:
        logger.error(f"Ошибка поиска телефонных номеров: {e}")
        return json.dumps([])


TRANSFER_CATEGORY = "Переводы"
PERSON_NAME_PATTERN = re.compile(r"[А-ЯЁ][а-яё]+ [А-Я]\.")


def search_person_transfers(transactions: List[Dict[str, Any]]) -> str:
    """Возвращает JSON со всеми транзакциями с категорией 'Переводы'"""

    try:
        filtered = filter(
            lambda tx: (
                tx.get("category", "") == TRANSFER_CATEGORY
                and "description" in tx
                and PERSON_NAME_PATTERN.search(tx["description"])
            ),
            transactions,
        )

        result = list(filtered)
        json_result = json.dumps(result, ensure_ascii=False)
        logger.info(f"Поиск переводов физлицам: найдено {len(result)} транзакций")
        return json_result

    except Exception as e:
        logger.error(f"Ошибка поиска переводов физлицам: {e}")
        return json.dumps([])
