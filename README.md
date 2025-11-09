# Техническое задание: Сбор данных о вакансиях в сфере искусственного интеллекта

## 1. Источники данных
- **API HeadHunter** (`api.hh.ru/vacancies`) - РЕАЛИЗОВАНО
- **API SuperJob** (`api.superjob.ru/2.0/vacancies/`)
- **API Habr Career** (`career.habr.com/api/v2/vacancies`)

## 2. Ограничения API (критически важные)
- **HeadHunter**: глубина истории - 30 дней, лимит - 2000 вакансий на запрос

## 3. Объем данных
- **Ожидаемая выборка**: 15,000-25,000+ вакансий совокупно
- **Критерий репрезентативности**: покрытие ключевых специализаций ИИ и всех месяцев периода

## 4. Параметры сбора

### 4.1. Поисковые запросы и фильтры
```python
search_keywords = [
    "искусственный интеллект", "AI", "Artificial Intelligence",
    "машинное обучение", "ML", "Machine Learning", 
    "Data Science", "Data Scientist",
    "глубокое обучение", "Deep Learning", "нейронная сеть",
    "компьютерное зрение", "Computer Vision", "CV",
    "обработка естественного языка", "NLP", "Natural Language Processing",
    "большие данные", "Big Data",
    "инженер данных", "Data Engineer",
    "MLOps", "ML Engineer", "AI Engineer",
    "AI Researcher", "Research Scientist"
]