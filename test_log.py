import pytest
import json
from unittest.mock import patch
from main import process_log_files, generate_report, main

@pytest.fixture
def sample_log_data():
    return [
        {"url": "/api/users", "response_time": 0.1},
        {"url": "/api/products", "response_time": 0.2},
        {"url": "/api/users", "response_time": 0.3},
    ]

@pytest.fixture
def create_log_file(tmp_path, sample_log_data):
    def _create_log_file(filename, data):
        file_path = tmp_path / filename
        with open(file_path, 'w') as f:
            for entry in data:
                f.write(json.dumps(entry) + '\n')
        return file_path
    return _create_log_file

def test_process_log_files_success(create_log_file, sample_log_data):
    log_file_path = create_log_file("test_log.log", sample_log_data)
    expected_stats = {
        "/api/users": {"count": 2, "total_response_time": 0.4},
        "/api/products": {"count": 1, "total_response_time": 0.2},
    }
    result = process_log_files([str(log_file_path)])
    assert result == expected_stats

def test_process_log_files_file_not_found():
    with patch('builtins.print') as mock_print:
        result = process_log_files(["nonexistent_file.log"])
        assert result == {}
        mock_print.assert_called_once_with("Файл не найден: nonexistent_file.log")

def test_process_log_files_json_decode_error(create_log_file):
    file_path = create_log_file("invalid_log.log", ["invalid json"])
    with patch('builtins.print') as mock_print:
        result = process_log_files([str(file_path)])
        assert result == {}
        mock_print.assert_called_once()

def test_process_log_files_key_error(create_log_file):
    data = [{"missing_url": "value", "response_time": 0.1}]
    file_path = create_log_file("missing_key.log", data)
    with patch('builtins.print') as mock_print:
        result = process_log_files([str(file_path)])
        assert result == {}
        mock_print.assert_called_once()

def test_generate_report(sample_log_data):
    endpoint_stats = {
        "/api/users": {"count": 2, "total_response_time": 0.4},
        "/api/products": {"count": 1, "total_response_time": 0.2},
    }
    expected_report = [
        [0, "/api/users", 2, "0.200"],
        [1, "/api/products", 1, "0.200"],
    ]
    report = generate_report(endpoint_stats)
    assert report == expected_report


def test_generate_report_empty_stats():
    report = generate_report({})
    assert report == []


@pytest.mark.parametrize(
    "cli_args, expected_output",
    [
        (
                "test_log.log",
                "Ошибка: Отсутствует ключ 'url' в файле ",
        ),
        (
                "nonexistent.log",
                "Файл не найден: ",
        ),
    ],
)
def test_main_errors(tmp_path, cli_args, expected_output, create_log_file, capsys):
    create_log_file('test_log.log', [{"wrong_key": "value", "response_time": 0.1}])
    file_path = tmp_path / cli_args
    with patch('sys.argv', ['main.py', '--file', str(file_path)]):
        try:
            main()
        except SystemExit:
            pass
        captured = capsys.readouterr()
    assert expected_output + str(file_path) in captured.out or expected_output + str(file_path) in captured.err


def test_main_success(tmp_path, capsys, create_log_file, sample_log_data):
    log_file_path = create_log_file("success_log.log", sample_log_data)
    with patch('sys.argv', ['main.py', '--file', str(log_file_path)]):
        main()
        captured = capsys.readouterr()

    assert "avg_response_time" in captured.out
    assert "0.2" in captured.out  # /api/users (0.1 + 0.3) / 2
    assert "0.2" in captured.out  # /api/products 0.2 / 1
