"""
Сервис визуализации данных с помощью matplotlib и seaborn
Генерация графиков и диаграмм для статистики рецептов
"""
from typing import Dict
import matplotlib
from typing import Dict
matplotlib.use('Agg')  # Использовать non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from io import BytesIO
import base64
from .models import Recipe, Ingredient
from .pandas_service import PandasDataService
from django.db.models import Count


class VisualizationService:
    """Сервис для создания визуализаций"""
    
    def __init__(self):
        sns.set_style('whitegrid')
        sns.set_palette('husl')
        plt.rcParams['figure.figsize'] = (12, 6)
        plt.rcParams['font.size'] = 10
    
    @staticmethod
    def _fig_to_base64(fig) -> str:
        """Конвертировать matplotlib figure в base64 строку для HTML"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close(fig)
        
        graphic = base64.b64encode(image_png).decode('utf-8')
        return graphic
    
    def plot_cooking_time_distribution(self) -> str:
        """
        График распределения времени приготовления рецептов
        """
        df = PandasDataService.recipes_to_dataframe()
        
        if df.empty:
            return ""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Гистограмма
        ax1.hist(df['cooking_time'], bins=20, edgecolor='black', alpha=0.7)
        ax1.set_xlabel('Время приготовления (минуты)')
        ax1.set_ylabel('Количество рецептов')
        ax1.set_title('Распределение времени приготовления')
        ax1.grid(True, alpha=0.3)
        
        # Box plot
        sns.boxplot(y=df['cooking_time'], ax=ax2, color='skyblue')
        ax2.set_ylabel('Время приготовления (минуты)')
        ax2.set_title('Box Plot времени приготовления')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def plot_servings_distribution(self) -> str:
        """
        График распределения количества порций
        """
        df = PandasDataService.recipes_to_dataframe()
        
        if df.empty:
            return ""
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        servings_counts = df['servings'].value_counts().sort_index()
        
        ax.bar(servings_counts.index, servings_counts.values, 
               edgecolor='black', alpha=0.7, color='coral')
        ax.set_xlabel('Количество порций')
        ax.set_ylabel('Количество рецептов')
        ax.set_title('Распределение рецептов по количеству порций')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def plot_top_ingredients(self, top_n: int = 15) -> str:
        """
        Столбчатая диаграмма топ ингредиентов
        """
        df = PandasDataService.ingredients_to_dataframe()
        
        if df.empty:
            return ""
        
        top_ingredients = df.nlargest(top_n, 'usage_count')
        
        fig, ax = plt.subplots(figsize=(12, 7))
        
        sns.barplot(
            data=top_ingredients,
            y='name',
            x='usage_count',
            ax=ax,
            palette='viridis'
        )
        
        ax.set_xlabel('Количество использований')
        ax.set_ylabel('Ингредиент')
        ax.set_title(f'Топ {top_n} наиболее используемых ингредиентов')
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def plot_recipes_by_author(self, top_n: int = 10) -> str:
        """
        График рецептов по авторам
        """
        df = PandasDataService.recipes_to_dataframe()
        
        if df.empty:
            return ""
        
        author_counts = df['author'].value_counts().head(top_n)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = sns.color_palette('Set2', len(author_counts))
        ax.pie(
            author_counts.values,
            labels=author_counts.index,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors
        )
        ax.set_title(f'Топ {top_n} авторов по количеству рецептов')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def plot_recipes_timeline(self) -> str:
        """
        График создания рецептов во времени
        """
        df = PandasDataService.recipes_to_dataframe()
        
        if df.empty:
            return ""
        
        df['month'] = df['created_at'].dt.to_period('M').astype(str)
        recipes_by_month = df.groupby('month').size()
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        ax.plot(range(len(recipes_by_month)), recipes_by_month.values, 
                marker='o', linewidth=2, markersize=8, color='steelblue')
        ax.fill_between(range(len(recipes_by_month)), recipes_by_month.values, 
                        alpha=0.3, color='steelblue')
        
        ax.set_xlabel('Месяц')
        ax.set_ylabel('Количество рецептов')
        ax.set_title('Динамика создания рецептов')
        ax.grid(True, alpha=0.3)
        
        if len(recipes_by_month) > 0:
            step = max(1, len(recipes_by_month) // 10)
            ax.set_xticks(range(0, len(recipes_by_month), step))
            ax.set_xticklabels(recipes_by_month.index[::step], rotation=45, ha='right')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def plot_cooking_time_vs_ingredients(self) -> str:
        """
        Scatter plot: время приготовления vs количество ингредиентов
        """
        df = PandasDataService.recipes_to_dataframe()
        
        if df.empty:
            return ""
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        scatter = ax.scatter(
            df['ingredients_count'],
            df['cooking_time'],
            alpha=0.6,
            s=100,
            c=df['servings'],
            cmap='viridis',
            edgecolors='black',
            linewidth=0.5
        )
        
        ax.set_xlabel('Количество ингредиентов')
        ax.set_ylabel('Время приготовления (минуты)')
        ax.set_title('Зависимость времени приготовления от количества ингредиентов')
        ax.grid(True, alpha=0.3)
        
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Количество порций')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def plot_correlation_heatmap(self) -> str:
        """
        Тепловая карта корреляций между параметрами рецептов
        """
        df = PandasDataService.recipes_to_dataframe()
        
        if df.empty or len(df) < 2:
            return ""
        
        numeric_cols = ['cooking_time', 'servings', 'ingredients_count']
        correlation_matrix = df[numeric_cols].corr()
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        sns.heatmap(
            correlation_matrix,
            annot=True,
            fmt='.2f',
            cmap='coolwarm',
            center=0,
            square=True,
            linewidths=1,
            cbar_kws={'label': 'Корреляция'},
            ax=ax
        )
        
        ax.set_title('Корреляция между параметрами рецептов')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def plot_ingredient_units_distribution(self) -> str:
        """
        Распределение единиц измерения ингредиентов
        """
        df = PandasDataService.ingredients_to_dataframe()
        
        if df.empty:
            return ""
        
        units_counts = df['unit'].value_counts()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        wedges, texts, autotexts = ax.pie(
            units_counts.values,
            labels=units_counts.index,
            autopct='%1.1f%%',
            startangle=90,
            colors=sns.color_palette('pastel')
        )
        
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(10)
        
        ax.set_title('Распределение единиц измерения ингредиентов')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def generate_all_visualizations(self) -> Dict:
        """
        Генерировать все визуализации
        """
        return {
            'cooking_time_distribution': self.plot_cooking_time_distribution(),
            'servings_distribution': self.plot_servings_distribution(),
            'top_ingredients': self.plot_top_ingredients(),
            'recipes_by_author': self.plot_recipes_by_author(),
            'recipes_timeline': self.plot_recipes_timeline(),
            'cooking_time_vs_ingredients': self.plot_cooking_time_vs_ingredients(),
            'correlation_heatmap': self.plot_correlation_heatmap(),
            'ingredient_units': self.plot_ingredient_units_distribution(),
        }

