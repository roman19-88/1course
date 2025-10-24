import sys
from unittest.mock import patch

import pytest

from src import main as main_module


@patch("src.main.generate_main_page_response")
def test_main_page_command_line(mock_generate_main):
    expected_response = {"greeting": "Тестовое приветствие"}
    mock_generate_main.return_value = expected_response

    testargs = ["src/main.py", "--page", "main", "--date", "2025-04-15"]
    with patch.object(sys, 'argv', testargs):
        response = main_module.main()

        mock_generate_main.assert_called_once()
        assert response == expected_response


@patch("src.main.simple_search")
def test_search_service_command_line(mock_search):
    expected_response = [{"Дата операции": "2025-04-15", "Сумма операции": -100, "Категория": "Рестораны", "Описание": "KFC"}]
    mock_search.return_value = '{"result": "test"}'

    testargs = ["src/main.py", "--service", "search", "--query", "KFC"]
    with patch.object(sys, 'argv', testargs):
        response = main_module.main()

        mock_search.assert_called_once()
        assert "result" in response
