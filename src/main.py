import argparse
import json
from datetime import datetime
from typing import Any, Dict

import pandas as pd

from src.reports import spending_by_category
from src.services import simple_search
from src.utils import logger
from src.views import generate_main_page_response


def load_transactions_somehow() -> list[Dict[str, Any]]:
    from src.utils import load_transactions
    df = load_transactions("data/operations.xlsx")
    return df.to_dict(orient="records")


def load_transactions_dataframe() -> pd.DataFrame:
    """Загружает транзакции и преобразует их в pandas DataFrame."""
    transactions_list = load_transactions_somehow()
    return pd.DataFrame(transactions_list)


def main() -> Dict[str, Any]:
    """Главная функция программы, парсит аргументы командной строки и
    генерирует соответствующий JSON-ответ"""

    parser = argparse.ArgumentParser(description="Генерация данных для финансовых отчетов и запуск сервисов")
    parser.add_argument("--page", choices=["main"], default="main",
                        help="Страница для генерации (только main)")
    parser.add_argument("--date", help="Дата в формате YYYY-MM-DD",
                        default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--service",
                        choices=["main", "search", "category_report"],
                        default=None,
                        help="Выбор сервиса для запуска")
    parser.add_argument("--query", help="Строка для поиска (требуется для service=search)")
    parser.add_argument("--category", help="Категория для отчета (требуется для service=category_report)")
    parser.add_argument("--output", help="Имя выходного файла для отчета")

    args = parser.parse_args()

    if args.service is None:
        args.service = "main"

    try:
        date_str = f"{args.date} 12:00:00"

        if args.service == "main":
            response = generate_main_page_response(date_str)

        elif args.service == "search":
            if not args.query:
                raise ValueError("Параметр --query обязателен для сервиса search")
            data = load_transactions_somehow()
            response_json = simple_search(args.query, data)
            response = json.loads(response_json)

        elif args.service == "category_report":
            if not args.category:
                raise ValueError("Параметр --category обязателен для отчета по категории")
            df = load_transactions_dataframe()

            if args.output:
                from src.reports import save_report
                custom_report = save_report(args.output)(spending_by_category)
                result_df = custom_report(df, args.category, args.date)
            else:
                result_df = spending_by_category(df, args.category, args.date)

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
