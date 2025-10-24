from typing import Any, Dict, List, Tuple

import pandas as pd

from src.utils import (
    filter_transactions_by_month,
    filter_transactions_by_period,
    get_currency_rates,
    get_greeting,
    get_stock_prices,
    load_transactions,
    load_user_settings,
    logger,
)


def get_card_info(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Получение информации о карте"""
    try:
        # Группируем транзакции по номеру карты и суммируем расходы
        card_groups = df.groupby("Номер карты")["Сумма операции"].sum().reset_index()

        cards_info = []
        for _, row in card_groups.iterrows():
            card_number = str(row["Номер карты"])

            last_digits = card_number[-4:] if len(card_number) >= 4 else card_number
            total_spent = float(row["Сумма операции"])

            # кэшбэк у меня равен 1% от общей суммы расходов
            cashback = round(abs(total_spent) * 0.01, 2)

            cards_info.append({
                "last_digits": last_digits,
                "total_spent": round(total_spent, 2),
                "cashback": cashback
            })

        logger.info(f"Получена информация о {len(cards_info)} картах")
        return cards_info
    except Exception as e:
        logger.error(f"Ошибка получения информации о картах: {e}")
        return []


def get_top_transactions(df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
    """Получение транзакций по сумме платежа"""
    try:
        # Сортируем транзакции по абсолютному значению суммы
        sorted_df = df.sort_values(by="Сумма операции", key=abs, ascending=False).head(limit)

        top_transactions = []
        for _, row in sorted_df.iterrows():
            transaction_date = row["Дата операции"]
            if isinstance(transaction_date, pd.Timestamp):
                formatted_date = transaction_date.strftime("%d.%m.%Y")
            else:
                formatted_date = str(transaction_date)

            top_transactions.append({
                "date": formatted_date,
                "amount": float(row["Сумма операции"]),
                "category": str(row["Категория"]),
                "description": str(row["Описание"])
            })

        logger.info(f"Получены топ-{limit} транзакции")
        return top_transactions
    except Exception as e:
        logger.error(f"Ошибка при получении топ транзакций: {e}")
        return []


def generate_main_page_response(date_str: str) -> Dict[str, Any]:
    """Генерация json ответа для главной страницы"""
    try:
        transaction_df = load_transactions("data/operations.xlsx")
        filtered_df = filter_transactions_by_month(transaction_df, date_str)
        greeting = get_greeting(date_str)
        cards_info = get_card_info(filtered_df)
        top_transactions = get_top_transactions(filtered_df, 5)
        user_settings = load_user_settings()
        currency_rates = get_currency_rates(user_settings.get("user_currencies", []))
        stock_prices = get_stock_prices(user_settings.get("user_stocks", []))

        response = {
            "greeting": greeting,
            "cards": cards_info,
            "top_transactions": top_transactions,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices
        }

        logger.info("Сформирован json ответ для главной страницы")
        return response
    except Exception as e:
        logger.error(f"Ошибка при создании json ответа: {e}")
        return {
            "greeting": "Произошла ошибка",
            "error": str(e),
            "cards": [],
            "top_transactions": [],
            "currency_rates": [],
            "stock_prices": []
        }


def get_expenses_income_data(df: pd.DataFrame) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Анализирует расходы и доходы из транзакций"""
    try:
        expenses_df = df[df["Сумма операции"] < 0].copy()
        income_df = df[df["Сумма операции"] > 0].copy()

        expenses_df["Сумма операции"] = expenses_df["Сумма операции"].abs()

        total_expenses = int(expenses_df["Сумма операции"].sum())
        total_income = int(income_df["Сумма операции"].sum())

        expenses_by_category = expenses_df.groupby("Категория")["Сумма операции"].sum().reset_index()
        expenses_by_category["Сумма операции"] = expenses_by_category["Сумма операции"].round().astype(int)
        expenses_by_category = expenses_by_category.sort_values(by="Сумма операции", ascending=False)

        income_by_category = income_df.groupby("Категория")["Сумма операции"].sum().reset_index()
        income_by_category["Сумма операции"] = income_by_category["Сумма операции"].round().astype(int)
        income_by_category = income_by_category.sort_values(by="Сумма операции", ascending=False)

        expenses_result = {
            "total_amount": total_expenses,
            "main": [],
            "transfers_and_cash": []
        }

        transfer_cash_categories = ['Переводы', 'Наличные']

        main_expenses = []
        transfers_cash = []
        other_expenses_sum = 0

        for _, row in expenses_by_category.iterrows():
            category = row["Категория"]
            amount = int(row["Сумма операции"])

            if category in transfer_cash_categories:
                transfers_cash.append({
                    "category": category,
                    "amount": amount
                })
            elif len(main_expenses) < 7:
                main_expenses.append({
                    "category": category,
                    "amount": amount
                })
            else:
                other_expenses_sum += amount

        if other_expenses_sum > 0:
            main_expenses.append({
                "category": "Остальное",
                "amount": other_expenses_sum
            })

        expenses_result["main"] = main_expenses
        expenses_result["transfers_and_cash"] = sorted(transfers_cash, key=lambda x: x["amount"], reverse=True)

        income_result = {
            "total_amount": total_income,
            "main": []
        }

        for _, row in income_by_category.iterrows():
            income_result["main"].append({
                "category": row["Категория"],
                "amount": int(row["Сумма операции"])
            })

        logger.info(f"Проанализированы расходы ({total_expenses}) и доходы ({total_income})")
        return expenses_result, income_result

    except Exception as e:
        logger.error(f"Ошибка при анализе расходов и доходов: {e}")
        return {
            "total_amount": 0,
            "main": [],
            "transfers_and_cash": []
        }, {
            "total_amount": 0,
            "main": []
        }


def generate_events_page_response(date_str: str, period: str = "M") -> Dict[str, Any]:
    """Генерация JSON-ответа для страницы события"""
    try:
        transaction_df = load_transactions("data/operations.xlsx")
        filtered_df = filter_transactions_by_period(transaction_df, date_str, period)

        expenses_data, income_data = get_expenses_income_data(filtered_df)

        user_settings = load_user_settings()
        currency_rates = get_currency_rates(user_settings.get("user_currencies", []))
        stock_prices = get_stock_prices(user_settings.get("user_stocks", []))

        response = {
            "expenses": expenses_data,
            "income": income_data,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices
        }

        logger.info(f"Сформирован JSON-ответ для страницы 'События' за период {period}")
        return response

    except Exception as e:
        logger.error(f"Ошибка при создании JSON-ответа для страницы 'События': {e}")
        return {
            "expenses": {"total_amount": 0, "main": [], "transfers_and_cash": []},
            "income": {"total_amount": 0, "main": []},
            "currency_rates": [],
            "stock_prices": []
        }
