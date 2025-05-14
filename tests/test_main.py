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


@patch("src.main.generate_events_page_response")
@pytest.mark.parametrize("period", ["W", "M", "Y", "ALL"])
def test_events_page_command_line(mock_generate_events, period):
    expected_response = {"expenses": {"total_amount": 1000}}
    mock_generate_events.return_value = expected_response

    testargs = ["src/main.py", "--page", "events", "--date", "2025-04-15", "--period", period]
    with patch.object(sys, 'argv', testargs):
        response = main_module.main()

        mock_generate_events.assert_called_once()
        assert response == expected_response
