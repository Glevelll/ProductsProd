"""
Сервис для парсинга рецептов с внешних сайтов
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re


class RecipeParserService:
    """Сервис для парсинга рецептов"""

    def __init__(self, url: str):
        self.url = url
        self.soup = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def fetch_page(self) -> bool:
        """Получает HTML-страницу"""
        try:
            response = requests.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()
            self.soup = BeautifulSoup(response.content, 'lxml')
            return True
        except Exception as e:
            print(f"Ошибка при загрузке страницы: {e}")
            return False

    def parse_recipe(self) -> Optional[Dict]:
        """
        Парсит рецепт с сайта
        Возвращает словарь с данными рецепта
        """
        if not self.fetch_page():
            return None

        recipe_data = {
            'title': self._extract_title(),
            'description': self._extract_description(),
            'instructions': self._extract_instructions(),
            'ingredients': self._extract_ingredients(),
            'cooking_time': self._extract_cooking_time(),
            'servings': self._extract_servings(),
        }

        if not recipe_data['title']:
            return None

        return recipe_data

    def _extract_title(self) -> str:
        """Извлекает название рецепта"""
        selectors = [
            'h1.recipe-title',
            'h1[itemprop="name"]',
            'h1.entry-title',
            '.recipe-header h1',
            'article h1',
            'h1',
        ]

        for selector in selectors:
            element = self.soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

        title_tag = self.soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            title = re.sub(r'\s*[|–-]\s*.+$', '', title)
            return title

        return "Рецепт без названия"

    def _extract_description(self) -> str:
        """Извлекает описание рецепта"""
        selectors = [
            'div.recipe-description',
            'div[itemprop="description"]',
            'meta[name="description"]',
            'meta[property="og:description"]',
            '.recipe-intro',
            'article p:first-of-type',
        ]

        for selector in selectors:
            if selector.startswith('meta'):
                element = self.soup.select_one(selector)
                if element and element.get('content'):
                    return element.get('content').strip()
            else:
                element = self.soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)

        paragraphs = self.soup.find_all('p', limit=3)
        if paragraphs:
            return paragraphs[0].get_text(strip=True)

        return "Описание отсутствует"

    def _extract_instructions(self) -> str:
        """Извлекает инструкции по приготовлению"""
        selectors = [
            'div.recipe-instructions',
            'div[itemprop="recipeInstructions"]',
            'ol.recipe-steps',
            'div.instructions',
            '.recipe-directions',
        ]

        for selector in selectors:
            element = self.soup.select_one(selector)
            if element:
                steps = []
                for i, step in enumerate(element.find_all(['li', 'p']), 1):
                    text = step.get_text(strip=True)
                    if text and len(text) > 10:
                        steps.append(f"{i}. {text}")
                if steps:
                    return '\n'.join(steps)

        all_text = self.soup.get_text()
        instructions_match = re.search(
            r'(Приготовление|Инструкция|Способ приготовления)[:\s]+(.*?)(?=Ингредиенты|$)',
            all_text,
            re.DOTALL | re.IGNORECASE
        )
        if instructions_match:
            return instructions_match.group(2).strip()

        return "Инструкции отсутствуют"

    def _extract_ingredients(self) -> List[Dict[str, str]]:
        """Извлекает список ингредиентов"""
        ingredients = []

        selectors = [
            'ul.recipe-ingredients',
            'ul[itemprop="recipeIngredient"]',
            'div.ingredients ul',
            '.ingredient-list',
        ]

        for selector in selectors:
            element = self.soup.select_one(selector)
            if element:
                for item in element.find_all('li'):
                    text = item.get_text(strip=True)
                    if text:
                        parsed = self._parse_ingredient_string(text)
                        if parsed:
                            ingredients.append(parsed)
                if ingredients:
                    return ingredients

        ingredient_items = self.soup.find_all(['li', 'p'], class_=re.compile('ingredient'))
        for item in ingredient_items:
            text = item.get_text(strip=True)
            if text:
                parsed = self._parse_ingredient_string(text)
                if parsed:
                    ingredients.append(parsed)

        if not ingredients:
            ingredients = [
                {'name': 'Ингредиент 1', 'quantity': '100', 'unit': 'г'},
                {'name': 'Ингредиент 2', 'quantity': '200', 'unit': 'мл'},
            ]

        return ingredients

    def _parse_ingredient_string(self, text: str) -> Optional[Dict[str, str]]:
        """Парсит строку ингредиента"""
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(г|мл|кг|л|шт|ст\.?\s*л\.?|ч\.?\s*л\.?|стакан\w*|штук\w*)\.?\s*[–—-]?\s*(.+)',
            r'(.+?)\s*[–—-]\s*(\d+(?:[.,]\d+)?)\s*(г|мл|кг|л|шт|ст\.?\s*л\.?|ч\.?\s*л\.?|стакан\w*|штук\w*)',
        ]

        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                if pattern == patterns[0]:
                    quantity, unit, name = match.groups()
                else:
                    name, quantity, unit = match.groups()

                quantity = quantity.replace(',', '.')
                name = name.strip()
                unit = self._normalize_unit(unit.strip())

                return {
                    'name': name,
                    'quantity': quantity,
                    'unit': unit,
                }

        if len(text) > 2:
            return {
                'name': text,
                'quantity': '1',
                'unit': 'шт',
            }

        return None

    def _normalize_unit(self, unit: str) -> str:
        """Нормализует единицы измерения"""
        unit_map = {
            'г': 'г',
            'гр': 'г',
            'грамм': 'г',
            'мл': 'мл',
            'кг': 'кг',
            'л': 'л',
            'литр': 'л',
            'шт': 'шт',
            'штук': 'шт',
            'ст.л': 'ст.л.',
            'ст л': 'ст.л.',
            'ч.л': 'ч.л.',
            'ч л': 'ч.л.',
            'стакан': 'стакан',
        }

        unit_lower = unit.lower().replace('.', '').replace(' ', '')
        for key, value in unit_map.items():
            if key.replace('.', '').replace(' ', '') == unit_lower:
                return value

        return unit

    def _extract_cooking_time(self) -> int:
        """Извлекает время приготовления"""
        selectors = [
            'time[itemprop="totalTime"]',
            'span.cooking-time',
            '.recipe-time',
        ]

        for selector in selectors:
            element = self.soup.select_one(selector)
            if element:
                text = element.get_text()
                match = re.search(r'(\d+)', text)
                if match:
                    return int(match.group(1))

        all_text = self.soup.get_text()
        time_match = re.search(r'(\d+)\s*мин', all_text)
        if time_match:
            return int(time_match.group(1))

        return 30

    def _extract_servings(self) -> int:
        """Извлекает количество порций"""
        selectors = [
            'span[itemprop="recipeYield"]',
            '.recipe-servings',
            '.servings',
        ]

        for selector in selectors:
            element = self.soup.select_one(selector)
            if element:
                text = element.get_text()
                match = re.search(r'(\d+)', text)
                if match:
                    return int(match.group(1))

        all_text = self.soup.get_text()
        servings_match = re.search(r'(\d+)\s*порц', all_text)
        if servings_match:
            return int(servings_match.group(1))

        return 4

