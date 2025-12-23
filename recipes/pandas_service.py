"""
Сервис для работы с данными через pandas
Экспорт, анализ и обработка данных рецептов
"""
import pandas as pd
import numpy as np
from django.db.models import Count, Avg
from .models import Recipe, Ingredient, RecipeIngredient, ShoppingList
from django.contrib.auth.models import User
from io import BytesIO
from typing import Dict, List


class PandasDataService:
    """Сервис для работы с данными через pandas"""
    
    @staticmethod
    def recipes_to_dataframe() -> pd.DataFrame:
        """
        Конвертировать все рецепты в pandas DataFrame
        """
        recipes = Recipe.objects.select_related('author').annotate(
            ingredients_count=Count('recipe_ingredients')
        ).values(
            'id', 'title', 'description', 'cooking_time', 'servings',
            'created_at', 'author__username', 'ingredients_count'
        )
        
        df = pd.DataFrame(list(recipes))
        
        if not df.empty:
            df.rename(columns={'author__username': 'author'}, inplace=True)
            df['created_at'] = pd.to_datetime(df['created_at'])
        
        return df
    
    @staticmethod
    def ingredients_to_dataframe() -> pd.DataFrame:
        """
        Конвертировать все ингредиенты в DataFrame
        """
        ingredients = Ingredient.objects.annotate(
            usage_count=Count('recipe_ingredients')
        ).values('id', 'name', 'unit', 'usage_count')
        
        df = pd.DataFrame(list(ingredients))
        return df
    
    @staticmethod
    def recipe_ingredients_to_dataframe() -> pd.DataFrame:
        """
        Конвертировать связи рецепт-ингредиент в DataFrame
        """
        recipe_ingredients = RecipeIngredient.objects.select_related(
            'recipe', 'ingredient'
        ).values(
            'id', 'recipe__title', 'ingredient__name', 
            'ingredient__unit', 'quantity'
        )
        
        df = pd.DataFrame(list(recipe_ingredients))
        
        if not df.empty:
            df.rename(columns={
                'recipe__title': 'recipe',
                'ingredient__name': 'ingredient',
                'ingredient__unit': 'unit'
            }, inplace=True)
        
        return df
    
    @staticmethod
    def get_recipe_statistics() -> Dict:
        """
        Получить детальную статистику по рецептам
        """
        df = PandasDataService.recipes_to_dataframe()
        
        if df.empty:
            return {
                'total_recipes': 0,
                'statistics': {}
            }
        
        stats = {
            'total_recipes': len(df),
            'statistics': {
                'cooking_time': {
                    'mean': round(df['cooking_time'].mean(), 2),
                    'median': round(df['cooking_time'].median(), 2),
                    'std': round(df['cooking_time'].std(), 2),
                    'min': int(df['cooking_time'].min()),
                    'max': int(df['cooking_time'].max()),
                },
                'servings': {
                    'mean': round(df['servings'].mean(), 2),
                    'median': round(df['servings'].median(), 2),
                    'min': int(df['servings'].min()),
                    'max': int(df['servings'].max()),
                },
                'ingredients_count': {
                    'mean': round(df['ingredients_count'].mean(), 2),
                    'median': round(df['ingredients_count'].median(), 2),
                    'min': int(df['ingredients_count'].min()),
                    'max': int(df['ingredients_count'].max()),
                }
            },
            'top_authors': df['author'].value_counts().head(10).to_dict(),
            'recipes_by_month': df.groupby(df['created_at'].dt.to_period('M')).size().to_dict()
        }
        
        return stats
    
    @staticmethod
    def get_ingredient_analysis() -> Dict:
        """
        Анализ использования ингредиентов
        """
        df = PandasDataService.ingredients_to_dataframe()
        
        if df.empty:
            return {'total_ingredients': 0}
        
        return {
            'total_ingredients': len(df),
            'most_used': df.nlargest(10, 'usage_count')[['name', 'usage_count']].to_dict('records'),
            'least_used': df.nsmallest(10, 'usage_count')[['name', 'usage_count']].to_dict('records'),
            'avg_usage': round(df['usage_count'].mean(), 2),
            'units_distribution': df['unit'].value_counts().to_dict()
        }
    
    @staticmethod
    def export_recipes_to_excel() -> BytesIO:
        """
        Экспортировать рецепты в Excel файл
        """
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            recipes_df = PandasDataService.recipes_to_dataframe()
            ingredients_df = PandasDataService.ingredients_to_dataframe()
            recipe_ingredients_df = PandasDataService.recipe_ingredients_to_dataframe()
            
            recipes_df.to_excel(writer, sheet_name='Recipes', index=False)
            ingredients_df.to_excel(writer, sheet_name='Ingredients', index=False)
            recipe_ingredients_df.to_excel(writer, sheet_name='Recipe_Ingredients', index=False)
        
        output.seek(0)
        return output
    
    @staticmethod
    def export_recipes_to_csv() -> str:
        """
        Экспортировать рецепты в CSV
        """
        df = PandasDataService.recipes_to_dataframe()
        return df.to_csv(index=False)
    
    @staticmethod
    def get_cooking_time_distribution(bins: int = 5) -> Dict:
        """
        Получить распределение рецептов по времени приготовления
        """
        df = PandasDataService.recipes_to_dataframe()
        
        if df.empty:
            return {}
        
        df['time_category'] = pd.cut(
            df['cooking_time'], 
            bins=bins, 
            labels=['Very Quick', 'Quick', 'Medium', 'Long', 'Very Long']
        )
        
        distribution = df['time_category'].value_counts().to_dict()
        return {str(k): v for k, v in distribution.items()}
    
    @staticmethod
    def get_user_shopping_analysis(user_id: int) -> Dict:
        """
        Анализ списка покупок пользователя
        """
        shopping_items = ShoppingList.objects.filter(
            user_id=user_id
        ).select_related('recipe')
        
        if not shopping_items.exists():
            return {'total_items': 0}
        
        recipes_data = []
        for item in shopping_items:
            recipes_data.append({
                'recipe_id': item.recipe.id,
                'recipe_title': item.recipe.title,
                'cooking_time': item.recipe.cooking_time,
                'servings': item.recipe.servings,
                'added_at': item.added_at
            })
        
        df = pd.DataFrame(recipes_data)
        df['added_at'] = pd.to_datetime(df['added_at'])
        
        return {
            'total_items': len(df),
            'total_cooking_time': int(df['cooking_time'].sum()),
            'total_servings': int(df['servings'].sum()),
            'avg_cooking_time': round(df['cooking_time'].mean(), 2),
            'recipes': df['recipe_title'].tolist()
        }
    
    @staticmethod
    def correlation_analysis() -> Dict:
        """
        Корреляционный анализ параметров рецептов
        """
        df = PandasDataService.recipes_to_dataframe()
        
        if df.empty or len(df) < 2:
            return {}
        
        numeric_cols = ['cooking_time', 'servings', 'ingredients_count']
        correlation_matrix = df[numeric_cols].corr()
        
        return correlation_matrix.to_dict()

