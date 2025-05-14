import argparse
import json
from datetime import datetime
from typing import Any, Dict

import pandas as pd

from src.reports import spending_by_category, spending_by_weekday, spending_by_workday
from src.services import (
    analyze_cashback_categories,
    investment_bank,
    search_person_transfers,
    search_phone_numbers,
    simple_search,
)
from src.utils import logger
from src.views import generate_events_page_response, generate_main_page_response


def load_transactions_somehow() -> list[Dict[str, Any]]:
    from src.utils import load_transactions
    return load_transactions("data/operations.xlsx")


def load_transactions_dataframe() -> pd.DataFrame:
    """Загружает транзакции и преобразует их в pandas DataFrame."""
    transactions_list = load_transactions_somehow()
    return pd.DataFrame(transactions_list)


def main() -> Dict[str, Any]:
    """Главная функция программы, парсит аргументы командной строки и
    генерирует соответствующий JSON-ответ"""

    parser = argparse.ArgumentParser(description="Генерация данных для финансовых отчетов и запуск сервисов")
    parser.add_argument("--page", choices=["main", "events"], default="main",
                        help="Страница для генерации (main или events)")
    parser.add_argument("--date", help="Дата в формате YYYY-MM-DD",
                        default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--period", choices=["W", "M", "Y", "ALL"], default="M",
                        help="Период для страницы events (W - неделя, M - месяц, Y - год, ALL - все данные)")
    parser.add_argument("--service",
                        choices=["main", "events", "cashback", "investment", "search", "phones", "transfers",
                                 "category_report", "weekday_report", "workday_report"],
                        default=None,
                        help="Выбор сервиса для запуска")
    parser.add_argument("--query", help="Строка для поиска (требуется для service=search)")
    parser.add_argument("--month", help="Месяц в формате YYYY-MM (требуется для service=investment)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Шаг округления для инвесткопилки (по умолчанию 10)")
    parser.add_argument("--category", help="Категория для отчета (требуется для service=category_report)")
    parser.add_argument("--output", help="Имя выходного файла для отчета")

    args = parser.parse_args()

    if args.service is None:
        args.service = args.page

    try:
        date_str = f"{args.date} 12:00:00"

        if args.page == "main" or args.service == "main":
            response = generate_main_page_response(date_str)

        elif args.page == "events" or args.service == "events":
            response = generate_events_page_response(date_str, args.period)

        elif args.service == "cashback":
            year = int(args.date.split("-")[0])
            month = int(args.date.split("-")[1])
            data = load_transactions_somehow()
            response_json = analyze_cashback_categories(data, year, month)
            response = json.loads(response_json)

        elif args.service == "investment":
            if not args.month:
                raise ValueError("Параметр --month обязателен для сервиса investment")
            data = load_transactions_somehow()
            savings = investment_bank(args.month, data, args.limit)
            response = {"investment_bank_savings": savings}

        elif args.service == "search":
            if not args.query:
                raise ValueError("Параметр --query обязателен для сервиса search")
            data = load_transactions_somehow()
            response_json = simple_search(args.query, data)
            response = json.loads(response_json)

        elif args.service == "phones":
            data = load_transactions_somehow()
            response_json = search_phone_numbers(data)
            response = json.loads(response_json)

        elif args.service == "transfers":
            data = load_transactions_somehow()
            response_json = search_person_transfers(data)
            response = json.loads(response_json)

        elif args.service == "category_report":
            if not args.category:
                raise ValueError("Параметр --category обязателен для отчета по категории")
            df = load_transactions_dataframe()

            if args.output:
                from functools import partial

                from src.reports import save_report
                custom_report = save_report(args.output)(spending_by_category)
                result_df = custom_report(df, args.category, args.date)
            else:
                result_df = spending_by_category(df, args.category, args.date)

            response = result_df.to_dict(orient="records")

        elif args.service == "weekday_report":
            df = load_transactions_dataframe()

            if args.output:
                from functools import partial

                from src.reports import save_report
                custom_report = save_report(args.output)(spending_by_weekday)
                result_df = custom_report(df, args.date)
            else:
                result_df = spending_by_weekday(df, args.date)

            response = result_df.to_dict(orient="records")

        elif args.service == "workday_report":
            df = load_transactions_dataframe()

            if args.output:
                from functools import partial

                from src.reports import save_report
                custom_report = save_report(args.output)(spending_by_workday)
                result_df = custom_report(df, args.date)
            else:
                result_df = spending_by_workday(df, args.date)

            response = result_df.to_dict(orient="records")

        else:
            raise ValueError("Неизвестный сервис")

        print(json.dumps(response, indent=2, ensure_ascii=False))
        logger.info(f"Программа успешно выполнена для сервиса {args.service}")
        return response

    except Exception as e:
        logger.error(f"Ошибка программы: {e}")
        response = {"error": str(e)}
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return response


if __name__ == "__main__":
    main()
