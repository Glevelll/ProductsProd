"""
Сервис для прямой работы с БД через dbAPI (psycopg2)
Демонстрация использования сырых SQL-запросов вместо Django ORM
"""
import psycopg2
from django.conf import settings
from typing import List, Dict, Optional


class DatabaseService:
    """Сервис для работы с БД через dbAPI"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Установить соединение с БД"""
        db_settings = settings.DATABASES['default']
        self.connection = psycopg2.connect(
            dbname=db_settings['NAME'],
            user=db_settings['USER'],
            password=db_settings['PASSWORD'],
            host=db_settings['HOST'],
            port=db_settings['PORT']
        )
        self.cursor = self.connection.cursor()
    
    def disconnect(self):
        """Закрыть соединение с БД"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        """Контекстный менеджер: вход"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход"""
        self.disconnect()
    
    def get_recipe_stats_raw(self) -> Dict:
        """
        Получить статистику по рецептам через сырой SQL
        Демонстрация dbAPI
        """
        query = """
        SELECT 
            COUNT(*) as total_recipes,
            AVG(cooking_time) as avg_cooking_time,
            MAX(cooking_time) as max_cooking_time,
            MIN(cooking_time) as min_cooking_time,
            AVG(servings) as avg_servings
        FROM recipes_recipe
        """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        
        return {
            'total_recipes': result[0],
            'avg_cooking_time': float(result[1]) if result[1] else 0,
            'max_cooking_time': result[2] if result[2] else 0,
            'min_cooking_time': result[3] if result[3] else 0,
            'avg_servings': float(result[4]) if result[4] else 0,
        }
    
    def get_top_ingredients_raw(self, limit: int = 10) -> List[Dict]:
        """
        Получить топ ингредиентов по использованию через сырой SQL
        """
        query = """
        SELECT 
            i.id,
            i.name,
            i.unit,
            COUNT(ri.id) as usage_count
        FROM recipes_ingredient i
        LEFT JOIN recipes_recipeingredient ri ON i.id = ri.ingredient_id
        GROUP BY i.id, i.name, i.unit
        ORDER BY usage_count DESC
        LIMIT %s
        """
        self.cursor.execute(query, (limit,))
        results = self.cursor.fetchall()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'unit': row[2],
                'usage_count': row[3]
            }
            for row in results
        ]
    
    def get_user_recipe_stats_raw(self, user_id: int) -> Dict:
        """
        Получить статистику по рецептам конкретного пользователя
        """
        query = """
        SELECT 
            COUNT(*) as total_recipes,
            AVG(cooking_time) as avg_cooking_time,
            SUM(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 ELSE 0 END) as recent_recipes
        FROM recipes_recipe
        WHERE author_id = %s
        """
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        
        return {
            'total_recipes': result[0],
            'avg_cooking_time': float(result[1]) if result[1] else 0,
            'recent_recipes': result[2],
        }
    
    def search_recipes_raw(self, search_term: str) -> List[Dict]:
        """
        Поиск рецептов через сырой SQL (Full-text search)
        """
        query = """
        SELECT 
            r.id,
            r.title,
            r.description,
            r.cooking_time,
            r.servings,
            u.username as author_name
        FROM recipes_recipe r
        JOIN auth_user u ON r.author_id = u.id
        WHERE 
            r.title ILIKE %s OR 
            r.description ILIKE %s OR 
            r.instructions ILIKE %s
        ORDER BY r.created_at DESC
        LIMIT 50
        """
        search_pattern = f'%{search_term}%'
        self.cursor.execute(query, (search_pattern, search_pattern, search_pattern))
        results = self.cursor.fetchall()
        
        return [
            {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'cooking_time': row[3],
                'servings': row[4],
                'author_name': row[5],
            }
            for row in results
        ]
    
    def get_shopping_list_summary_raw(self, user_id: int) -> List[Dict]:
        """
        Получить суммированный список покупок пользователя через SQL
        """
        query = """
        SELECT 
            i.name,
            i.unit,
            SUM(ri.quantity) as total_quantity
        FROM recipes_shoppinglist sl
        JOIN recipes_recipe r ON sl.recipe_id = r.id
        JOIN recipes_recipeingredient ri ON ri.recipe_id = r.id
        JOIN recipes_ingredient i ON ri.ingredient_id = i.id
        WHERE sl.user_id = %s
        GROUP BY i.id, i.name, i.unit
        ORDER BY i.name
        """
        self.cursor.execute(query, (user_id,))
        results = self.cursor.fetchall()
        
        return [
            {
                'name': row[0],
                'unit': row[1],
                'total_quantity': float(row[2])
            }
            for row in results
        ]
    
    def execute_custom_query(self, query: str, params: tuple = None) -> List[tuple]:
        """
        Выполнить произвольный SQL-запрос
        ВНИМАНИЕ: использовать осторожно, риск SQL-инъекций!
        """
        self.cursor.execute(query, params)
        return self.cursor.fetchall()


def get_recipe_stats_via_dbapi() -> Dict:
    """
    Вспомогательная функция для получения статистики через dbAPI
    """
    with DatabaseService() as db:
        return db.get_recipe_stats_raw()


def get_top_ingredients_via_dbapi(limit: int = 10) -> List[Dict]:
    """
    Вспомогательная функция для получения топ ингредиентов через dbAPI
    """
    with DatabaseService() as db:
        return db.get_top_ingredients_raw(limit)

