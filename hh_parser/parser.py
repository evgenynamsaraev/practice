import requests
import random
import time
import logging

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class HHApiGetter:
    """Парсер вакансий с HeadHunter API для сферы ИИ"""

    def __init__(self):
        self.base_url = "https://api.hh.ru/vacancies"
        self.session = requests.Session()

        # Ротация User-Agent
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]

        self.update_headers()

        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('hh_parser.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        self.vacancies_data = []
        self.request_count = 0

        self.search_keywords = [
            "искусственный интеллект",
        ]

    def update_headers(self):
        """Обновление заголовков с случайным User-Agent"""

        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://hh.ru/',
            'Accept-Encoding': 'gzip, deflate, br'
        })

    def _do_request(self, url: str, params: Dict = None, max_retries: int = 5) -> Optional[Dict]:
        """Безопасный запрос с повторными попытками и экспоненциальной задержкой"""

        for attempt in range(max_retries):
            try:
                self.request_count += 1

                # Случайная задержка между запросами
                delay = random.uniform(1.0, 3.0)  # 1-3 секунды между запросами
                time.sleep(delay)

                # Периодически обновляем User-Agent
                if self.request_count % 10 == 0:
                    self.update_headers()

                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 403:
                    self.logger.warning(f"Получен 403 Forbidden. Попытка {attempt + 1}/{max_retries}")

                    if 'captcha_url' in response.text:
                        self.logger.error("Требуется ввод капчи. Прерывание.")
                        return None

                    # Экспоненциальная задержка при 403
                    wait_time = (2 ** attempt) + random.uniform(1, 3)
                    self.logger.info(f"Ожидание {wait_time:.1f} секунд перед повторной попыткой")
                    time.sleep(wait_time)

                elif response.status_code == 400:
                    # Часто возникает при неправильных параметрах даты
                    error_data = response.json()
                    self.logger.error(f"Ошибка 400: {error_data}")
                    return None

                else:
                    self.logger.warning(f"HTTP {response.status_code}. Попытка {attempt + 1}/{max_retries}")
                    time.sleep((2 ** attempt) + random.uniform(1, 2))

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Ошибка сети: {e}. Попытка {attempt + 1}/{max_retries}")
                time.sleep((2 ** attempt) + random.uniform(1, 2))

        self.logger.error(f"Не удалось выполнить запрос после {max_retries} попыток")
        return None

    def search_vacancies(self, keyword: str, date_from: str, date_to: str, page: int = 0) -> Optional[Dict]:
        """Поиск вакансий с безопасными параметрами"""

        # Ограничиваем глубину поиска 1 месяцем для избежания ошибок
        params = {
            'text': f'"{keyword}"',
            'search_field': 'name',
            'per_page': 50,
            'page': page,
            'specialization': 1,  # IT
            'only_with_salary': False
        }

        # Добавляем даты только если период небольшой
        days_diff = (datetime.strptime(date_to, '%Y-%m-%d') - datetime.strptime(date_from, '%Y-%m-%d')).days
        if days_diff <= 30:  # Только для периодов до 30 дней
            params.update({
                'date_from': date_from,
                'date_to': date_to
            })

        return self._do_request(self.base_url, params)

    def collect_data_safely(self, days_back: int = 30) -> List[Dict]:
        """Cбор данных с ограничением по времени"""

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        self.logger.info(f"Cбор данных с {start_date} по {end_date}")

        for keyword in self.search_keywords:
            self.logger.info(f"Обработка ключевого слова: {keyword}")

            page = 0
            total_pages = 1

            while page < total_pages and page < 10:  # Ограничение 10 страниц
                self.logger.info(f"Страница {page + 1}")

                search_results = self.search_vacancies(keyword, start_date, end_date, page)

                if not search_results:
                    self.logger.warning(f"Пустой ответ для '{keyword}', страница {page}")
                    break

                if 'errors' in search_results:
                    self.logger.error(f"Ошибка API: {search_results['errors']}")
                    break

                vacancies = search_results.get('items', [])
                found = search_results.get('found', 0)
                total_pages = search_results.get('pages', 1)

                self.logger.info(f"Найдено: {found}, страниц: {total_pages}")

                # Ограничиваем обработку первых N вакансий на странице
                for i, vacancy in enumerate(vacancies[:20]):  # Только первые 20 на странице
                    if len(self.vacancies_data) >= 500:  # Общее ограничение
                        self.logger.info("Достигнут лимит в 500 вакансий")
                        break

                    parsed_vacancy = self.parse_vacancy(vacancy, keyword)
                    if parsed_vacancy:
                        self.vacancies_data.append(parsed_vacancy)

                    # Задержка между обработкой вакансий
                    time.sleep(random.uniform(0.5, 1.5))

                page += 1

                # Большая пауза между страницами
                time.sleep(random.uniform(2, 4))

        return self.vacancies_data

    def get_vacancy_details(self, vacancy_id: str) -> Optional[Dict]:
        """Получение детальной информации о вакансии"""

        params = {}

        self.logger.info(f"Запрос для id вакансии = '{vacancy_id}'")

        return self._do_request(f"{self.base_url}/{vacancy_id}", params)

    def parse_vacancy(self, vacancy: Dict, keyword: str) -> Dict[str, Any]:
        """Парсинг основной информации о вакансии"""

        # Получаем детальную информацию
        details = self.get_vacancy_details(vacancy['id'])
        if not details:
            return {}

        salary_info = self.parse_salary(vacancy.get('salary'))
        skills = self.parse_skills(details)

        # Определяем удаленную работу (исправленная часть)
        schedule = self.parse_schedule(vacancy.get('schedule'))
        is_remote = 'удаленная работа' in schedule.lower()

        # Дополнительная проверка по адресу (с защитой от None)
        if not is_remote:
            addresses = details.get('address', []) or []
            for addr in addresses:
                if addr and isinstance(addr, dict):  # Проверяем, что адрес не None и это словарь
                    metro_info = addr.get('metro')
                    if metro_info and isinstance(metro_info, dict):
                        station_name = metro_info.get('station_name', '')
                        if station_name and 'удален' in station_name.lower():
                            is_remote = True
                            break

        parsed_vacancy = {
            'vacancy_id': vacancy['id'],
            'source': 'HeadHunter',
            'url': vacancy['alternate_url'],
            'created_at': vacancy['created_at'],
            'published_at': vacancy['published_at'],
            'year_published': datetime.strptime(vacancy['published_at'][:10], '%Y-%m-%d').year,
            'month_published': datetime.strptime(vacancy['published_at'][:10], '%Y-%m-%d').month,

            # Основная информация
            'position': vacancy['name'],
            'company_name': vacancy['employer']['name'],
            'area_id': vacancy['area']['id'],
            'area_name': vacancy['area']['name'],

            # Опыт и зарплата
            'experience': self.parse_experience(vacancy.get('experience')),
            **salary_info,

            # Занятость
            'employment_type': self.parse_employment(vacancy.get('employment')),
            'schedule_type': schedule,
            'remote': is_remote,

            # Навыки и описание
            'skills': skills,
            'skills_count': len(skills),
            'description_raw': details.get('description', ''),
            'description_clean': self.clean_html(details.get('description', '')),

            # Образование
            'education_requirement': self.get_education_requirement(details),

            # Дополнительная информация
            'search_keyword': keyword,
            'response_url': vacancy.get('response_url'),
            'employer_id': vacancy['employer']['id'],
            'has_test': vacancy.get('has_test', False),
            'response_letter_required': vacancy.get('response_letter_required', False)
        }

        return parsed_vacancy

    def parse_salary(self, salary_data: Optional[Dict]) -> Dict:
        """Парсинг информации о зарплате"""
        if not salary_data:
            return {
                "salary_from": None,
                "salary_to": None,
                "salary_currency": None,
                "gross": None
            }

        return {
            "salary_from": salary_data.get("from"),
            "salary_to": salary_data.get("to"),
            "salary_currency": salary_data.get("currency"),
            "gross": salary_data.get("gross")
        }

    def parse_experience(self, experience_data: Optional[Dict]) -> str:
        """Парсинг информации об опыте работы"""
        return experience_data.get("name", "Не указан") if experience_data else "Не указан"

    def parse_employment(self, employment_data: Optional[Dict]) -> str:
        """Парсинг типа занятости"""
        return employment_data.get("name", "Не указан") if employment_data else "Не указан"

    def parse_schedule(self, schedule_data: Optional[Dict]) -> str:
        """Парсинг графика работы"""
        schedule_name = schedule_data.get('name', 'Не указан') if schedule_data else 'Не указан'
        return 'удаленная работа' if 'удален' in schedule_name.lower() else schedule_name

    def parse_skills(self, vacancy_details: Dict) -> List[str]:
        """Парсинг ключевых навыков"""
        skills = vacancy_details.get("key_skills", [])
        return [skill["name"] for skill in skills]

    def clean_html(self, html_text: str) -> str:
        """Очистка HTML тегов из описания"""
        import re
        clean = re.compile("<.*?>")
        return re.sub(clean, "", html_text)

    def get_education_requirement(self, details: Dict) -> str:
        """Получение требований к образованию"""
        # В HH API нет прямого поля, ищем в описании
        description = details.get("description", "").lower()
        if "высшее образование" in description:
            return "высшее"
        elif "среднее специальное" in description:
            return "среднее специальное"
        else:
            return "не указано"
