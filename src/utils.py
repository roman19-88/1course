import datetime
import json
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

_cache: Dict[Any, Any] = {}
_cache_time: Dict[Any, float] = {}


def get_currency_rates(
    currencies: List[str],
) -> List[Dict[str, Union[str, float]]]:
    """Получает курсы валют с использованием ключа API из .env файла"""
    try:

        def fetch_data() -> Dict[str, Any]:
            api_key = os.getenv("EXCHANGE_API_KEY", "")
            url = "https://open.er-api.com/v6/latest/RUB"
            headers = {}

            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Ошибка API: Статус {response.status_code}")
                return {"rates": {}}
            return response.json()

        data = with_cache(fetch_data, "currency_rates", ttl=3600)

        result: List[Dict[str, Union[str, float]]] = []
        for curr in currencies:
            if curr in data.get("rates", {}):
                rate = round(1 / data["rates"][curr], 2)
                result.append({"currency": curr, "rate": rate})
            else:
                logger.warning(f"Валюта {curr} не найдена в ответе API")
                result.append({"currency": curr, "rate": 0.0})

        logger.info(f"Получены курсы валют: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении курсов валют: {e}")
        return [{"currency": curr, "rate": 0.0} for curr in currencies]


def with_cache(func: Callable[[], Any], cache_key: Any, ttl: int = 300) -> Any:
    """Кэширует результаты функции на указанное время"""
    current_time = time.time()
    if cache_key in _cache and current_time - _cache_time[cache_key] < ttl:
        logger.debug(f"Используются кэшированные данные для {cache_key}")
        return _cache[cache_key]

    result = func()
    _cache[cache_key] = result
    _cache_time[cache_key] = current_time
    return result


def load_transactions(file_path: str) -> pd.DataFrame:
    """Загружает транзакции из Excel-файла"""
    try:
        abs_file_path = os.path.join(BASE_DIR, file_path)
        logger.info(f"Загрузка данных из {abs_file_path}")

        if os.path.exists(abs_file_path):
            df = pd.read_excel(abs_file_path)
            logger.info(f"Доступные колонки: {df.columns.tolist()}")

            required_columns = ["date", "card", "amount", "category", "description"]
            missing_columns = False

            for required in required_columns:
                if not any(required in col.lower() for col in df.columns):
                    logger.warning(f"В файле отсутствует колонка {required}")
                    missing_columns = True
                    break

            if not missing_columns:
                date_column = [col for col in df.columns if "date" in col.lower()][0]
                df[date_column] = pd.to_datetime(df[date_column])
                logger.info(f"Успешно загружено {len(df)} транзакций")
                return df

        logger.warning(
            "Файл не найден или отсутствуют нужные колонки. Создаю тестовые данные."
        )

        now = datetime.datetime.now()
        start_of_month = now.replace(day=1)

        import random

        dates: List[datetime.datetime] = []
        card_numbers: List[str] = []
        amounts: List[float] = []
        categories: List[str] = []
        descriptions: List[str] = []

        for _ in range(20):
            day_delta = random.randint(0, (now - start_of_month).days)
            date = start_of_month + datetime.timedelta(days=day_delta)
            dates.append(date)

            card_numbers.append(random.choice(["1234567890123456", "9876543210987654"]))
            amounts.append(round(random.uniform(-1000, 1000), 2))

            category = random.choice(
                [
                    "Рестораны",
                    "Супермаркеты",
                    "Развлечения",
                    "Транспорт",
                    "ЖКХ",
                    "Переводы",
                    "Зарплата",
                ]
            )
            categories.append(category)

            if category == "Рестораны":
                descriptions.append(random.choice(["KFC", "Макдоналдс", "Суши"]))
            elif category == "Супермаркеты":
                descriptions.append(random.choice(["Пятерочка", "Магнит", "Лента"]))
            else:
                descriptions.append(f"Описание для {category}")

        test_data = {
            "date": dates,
            "card_number": card_numbers,
            "amount": amounts,
            "category": categories,
            "description": descriptions,
        }

        test_df = pd.DataFrame(test_data)

        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
        test_df.to_excel(abs_file_path, index=False)
        logger.info(f"Созданы и сохранены тестовые данные ({len(test_df)} записей)")
        return test_df

    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        return pd.DataFrame(
            {
                "date": [datetime.datetime.now()],
                "card_number": ["1234567890123456"],
                "amount": [100.0],
                "category": ["Тест"],
                "description": ["Тестовая запись"],
            }
        )


def filter_transactions_by_month(df: pd.DataFrame, date_str: str) -> pd.DataFrame:
    """Фильтрует транзакции с начала месяца по указанную дату"""
    try:
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        start_date = target_date.replace(day=1, hour=0, minute=0, second=0)
        date_column = [col for col in df.columns if "date" in col.lower()][0]
        filtered_df = df[(df[date_column] >= start_date) & (df[date_column] <= target_date)]

        logger.info(
            f"Отфильтровано {len(filtered_df)} транзакций с "
            f"{start_date.strftime('%Y-%m-%d')} по {target_date.strftime('%Y-%m-%d')}"
        )
        return filtered_df
    except Exception as e:
        logger.error(f"Ошибка при фильтрации транзакций: {e}")
        raise


def get_greeting(time_str: str) -> str:
    """Определяет приветствие в зависимости от времени суток"""
    hour = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").hour

    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def load_user_settings() -> Dict[str, List[str]]:
    """Загружает пользовательские настройки из JSON-файла"""
    try:
        settings_path = os.path.join(BASE_DIR, "user_settings.json")
        with open(settings_path, "r", encoding="utf-8") as f:
            settings: Dict[str, List[str]] = json.load(f)
        logger.info(f"Загружены пользовательские настройки: {settings}")
        return settings
    except Exception as e:
        logger.error(f"Ошибка при загрузке пользовательских настроек: {e}")
        return {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"],
        }


def get_currency_rates(
    currencies: List[str],
) -> List[Dict[str, Union[str, float]]]:
    """Получает курсы валют"""
    try:

        def fetch_data() -> Dict[str, Any]:
            url = "https://open.er-api.com/v6/latest/RUB"
            response = requests.get(url)
            if response.status_code != 200:
                logger.error(f"Ошибка API: Статус {response.status_code}")
                return {"rates": {}}
            return response.json()

        data = with_cache(fetch_data, "currency_rates", ttl=3600)

        result: List[Dict[str, Union[str, float]]] = []
        for curr in currencies:
            if curr in data.get("rates", {}):
                rate = round(1 / data["rates"][curr], 2)
                result.append({"currency": curr, "rate": rate})
            else:
                logger.warning(f"Валюта {curr} не найдена в ответе API")
                result.append({"currency": curr, "rate": 0.0})

        logger.info(f"Получены курсы валют: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении курсов валют: {e}")
        return [{"currency": curr, "rate": 0.0} for curr in currencies]


try:
    import yfinance as yf
    use_yfinance = True
except ImportError:
    logger.warning("Библиотека yfinance не установлена, используются демо-данные")
    use_yfinance = False


def get_stock_prices(
    stocks: List[str],
) -> List[Dict[str, Union[str, float]]]:
    """Получает текущие цены на акции"""
    try:
        if use_yfinance:
            result: List[Dict[str, Union[str, float]]] = []
            for stock in stocks:

                def fetch_stock_data(ticker: str = stock) -> Optional[float]:
                    stock_data = yf.Ticker(ticker)
                    hist = stock_data.history(period="1d")
                    if hist.empty:
                        return None
                    return float(hist["Close"].iloc[-1])

                price = with_cache(fetch_stock_data, f"stock_price_{stock}", ttl=3600)

                if price is not None:
                    result.append({"stock": stock, "price": round(price, 2)})
                else:
                    logger.warning(f"Не удалось получить данные для акции {stock}")
                    result.append({"stock": stock, "price": 0.0})

            return result

        demo_prices: Dict[str, float] = {
            "AAPL": 150.12,
            "AMZN": 3173.18,
            "GOOGL": 2742.39,
            "MSFT": 296.71,
            "TSLA": 1007.08,
        }

        result = []
        for stock in stocks:
            if stock in demo_prices:
                result.append({"stock": stock, "price": demo_prices[stock]})
            else:
                logger.warning(f"Тикер акции {stock} не найден")
                result.append({"stock": stock, "price": 0.0})

        logger.info(f"Получены цены акций (демо): {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении цен акций: {e}")
        return [{"stock": stock, "price": 0.0} for stock in stocks]


def filter_transactions_by_period(
    df: pd.DataFrame, date_str: str, period: str = "M"
) -> pd.DataFrame:
    """ Фильтрует транзакции по указанному периоду"""
    try:
        if not isinstance(date_str, str):
            date_str = date_str.strftime("%Y-%m-%d %H:%M:%S")

        target_date = datetime.datetime.strptime(date_str.split()[0], "%Y-%m-%d")
        date_column = [col for col in df.columns if "date" in col.lower()][0]

        if period == "W":
            start_date = target_date - datetime.timedelta(days=target_date.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0)
            logger.info(
                f"Фильтрация по неделе: с {start_date.strftime('%Y-%m-%d')} "
                f"по {target_date.strftime('%Y-%m-%d')}"
            )
        elif period == "M":
            start_date = target_date.replace(day=1, hour=0, minute=0, second=0)
            logger.info(
                f"Фильтрация по месяцу: с {start_date.strftime('%Y-%m-%d')} "
                f"по {target_date.strftime('%Y-%m-%d')}"
            )
        elif period == "Y":
            start_date = target_date.replace(month=1, day=1, hour=0, minute=0, second=0)
            logger.info(
                f"Фильтрация по году: с {start_date.strftime('%Y-%m-%d')} "
                f"по {target_date.strftime('%Y-%m-%d')}"
            )
        elif period == "ALL":
            start_date = datetime.datetime(1900, 1, 1)
            logger.info(f"Фильтрация по всем данным до {target_date.strftime('%Y-%m-%d')}")
        else:
            start_date = target_date.replace(day=1, hour=0, minute=0, second=0)
            logger.info(
                f"Неизвестный период '{period}', используется месяц: "
                f"с {start_date.strftime('%Y-%m-%d')} "
                f"по {target_date.strftime('%Y-%m-%d')}"
            )

        filtered_df = df[(df[date_column] >= start_date) & (df[date_column] <= target_date)]
        logger.info(f"Отфильтровано {len(filtered_df)} транзакций за период {period}")
        return filtered_df
    except Exception as e:
        logger.error(f"Ошибка при фильтрации транзакций по периоду: {e}")
        raise
