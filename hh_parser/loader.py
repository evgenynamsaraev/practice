import pandas as pd
import json
import logging
import os

from typing import List, Dict


class Loader:
    def __init__(self, vacancies_data: List[Dict]):
        self.logger = logging.getLogger(__name__)
        self.vacancies_data = vacancies_data

    def save_to_jsonl(self, filename: str):
        """Сохранение данных в JSONL формате"""
        os.makedirs("data/raw/hh", exist_ok=True)
        filepath = f"data/raw/hh/{filename}"

        with open(filepath, "w", encoding="utf-8") as f:
            for vacancy in self.vacancies_data:
                f.write(json.dumps(vacancy, ensure_ascii=False) + "\n")

        self.logger.info(f"Данные сохранены в {filepath}")

    def save_to_csv(self, filename: str):
        """Сохранение данных в CSV формате"""
        os.makedirs("data/processed", exist_ok=True)
        filepath = f"data/processed/{filename}"

        df = pd.DataFrame(self.vacancies_data)

        # Обработка списка навыков для CSV
        if "skills" in df.columns:
            df["skills"] = df["skills"].apply(lambda x: "; ".join(x) if isinstance(x, list) else "")

        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        self.logger.info(f"Данные сохранены в {filepath}")