import argparse
import json
from tabulate import tabulate

def process_log_files(log_files):

    endpoint_stats = {}
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        url = log_entry['url']
                        response_time = log_entry['response_time']

                        if url not in endpoint_stats:
                            endpoint_stats[url] = {'count': 0, 'total_response_time': 0.0}

                        endpoint_stats[url]['count'] += 1
                        endpoint_stats[url]['total_response_time'] += response_time
                    except json.JSONDecodeError:
                        print(f"Ошибка при разборе JSON в файле {log_file}: {line.strip()}")
                    except KeyError as e:
                        print(f"Ошибка: Отсутствует ключ {e} в файле {log_file}")
        except FileNotFoundError:
            print(f"Файл не найден: {log_file}")
        except Exception as e:
            print(f"Ошибка при обработке файла {log_file}: {e}")

    return endpoint_stats


def generate_report(endpoint_stats):

    report_data = []
    index = 0
    for url, stats in endpoint_stats.items():
        count = stats['count']
        total_response_time = stats['total_response_time']
        avg_response_time = total_response_time / count if count > 0 else 0.0
        report_data.append([index, url, count, f"{avg_response_time:.3f}"])

        index += 1

    return report_data


def main():
    parser = argparse.ArgumentParser(description='Обработка лог-файлов и формирование отчета по эндпоинтам.')
    parser.add_argument('--file', dest='log_files', nargs='+', required=True,
                        help='Список лог-файлов для обработки.')
    parser.add_argument('--report', dest='report_name', default='average',
                        help='Название отчета (используется только для именования файла, в консоль всегда выводится).')

    args = parser.parse_args()

    endpoint_stats = process_log_files(args.log_files)
    report_data = generate_report(endpoint_stats)

    headers = ['handler', 'url', 'total', 'avg_response_time']
    print(tabulate(report_data, headers=headers))


if __name__ == "__main__":
    main()

