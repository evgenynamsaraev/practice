from datetime import datetime

from hh_parser.parser import HHApiGetter
from hh_parser.loader import Loader


def main():
    """Основная функция для сбора данных за год"""

    parser = HHApiGetter()

    try:
        vacancies = parser.collect_data_safely(days_back=14)  # 2 недели

        if vacancies:
            loader = Loader(vacancies)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            loader.save_to_jsonl(f"hh_vacancies_{timestamp}.jsonl")
            loader.save_to_csv(f"ai_vacancies_{timestamp}.csv")

            print(f"Успешно собрано: {len(vacancies)} вакансий")

    except Exception as e:
        parser.logger.error(f"Критическая ошибка: {e}")


if __name__ == "__main__":
    main()
