"""
Сервис машинного обучения для рекомендаций рецептов
Использует scikit-learn для анализа и рекомендаций
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from typing import List, Dict
from .models import Recipe, Ingredient, RecipeIngredient
from django.db.models import Count


class RecipeRecommendationService:
    """Сервис для рекомендаций рецептов на основе ML"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words=None,
            ngram_range=(1, 2)
        )
    
    def get_recipe_features(self, recipe: Recipe) -> str:
        """
        Получить текстовое представление рецепта для анализа
        """
        ingredients = ' '.join([
            ri.ingredient.name 
            for ri in recipe.recipe_ingredients.all()
        ])
        
        features = f"{recipe.title} {recipe.description} {ingredients}"
        return features
    
    def recommend_similar_recipes(self, recipe_id: int, top_n: int = 5) -> List[Dict]:
        """
        Рекомендовать похожие рецепты на основе TF-IDF и косинусного сходства
        """
        try:
            target_recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return []
        
        all_recipes = Recipe.objects.prefetch_related('recipe_ingredients__ingredient').all()
        
        if len(all_recipes) < 2:
            return []
        
        recipe_texts = []
        recipe_ids = []
        
        for recipe in all_recipes:
            recipe_texts.append(self.get_recipe_features(recipe))
            recipe_ids.append(recipe.id)
        
        tfidf_matrix = self.vectorizer.fit_transform(recipe_texts)
        
        target_idx = recipe_ids.index(recipe_id)
        target_vector = tfidf_matrix[target_idx]
        
        similarities = cosine_similarity(target_vector, tfidf_matrix).flatten()
        
        similar_indices = similarities.argsort()[-top_n-1:-1][::-1]
        
        recommendations = []
        for idx in similar_indices:
            if recipe_ids[idx] != recipe_id:
                recipe = all_recipes[idx]
                recommendations.append({
                    'id': recipe.id,
                    'title': recipe.title,
                    'similarity_score': round(float(similarities[idx]), 4),
                    'cooking_time': recipe.cooking_time,
                    'servings': recipe.servings,
                })
        
        return recommendations[:top_n]
    
    def recommend_by_ingredients(self, ingredient_ids: List[int], top_n: int = 5) -> List[Dict]:
        """
        Рекомендовать рецепты на основе выбранных ингредиентов
        """
        if not ingredient_ids:
            return []
        
        recipes = Recipe.objects.filter(
            recipe_ingredients__ingredient_id__in=ingredient_ids
        ).annotate(
            matching_ingredients=Count('recipe_ingredients')
        ).order_by('-matching_ingredients').distinct()[:top_n]
        
        recommendations = []
        for recipe in recipes:
            total_ingredients = recipe.recipe_ingredients.count()
            match_percentage = (recipe.matching_ingredients / total_ingredients * 100) if total_ingredients > 0 else 0
            
            recommendations.append({
                'id': recipe.id,
                'title': recipe.title,
                'matching_ingredients': recipe.matching_ingredients,
                'total_ingredients': total_ingredients,
                'match_percentage': round(match_percentage, 2),
                'cooking_time': recipe.cooking_time,
                'servings': recipe.servings,
            })
        
        return recommendations
    
    def cluster_recipes(self, n_clusters: int = 5) -> Dict:
        """
        Кластеризация рецептов с помощью K-Means
        """
        recipes = Recipe.objects.prefetch_related('recipe_ingredients__ingredient').all()
        
        if len(recipes) < n_clusters:
            return {'error': 'Not enough recipes for clustering'}
        
        recipe_texts = []
        recipe_data = []
        
        for recipe in recipes:
            recipe_texts.append(self.get_recipe_features(recipe))
            recipe_data.append({
                'id': recipe.id,
                'title': recipe.title,
                'cooking_time': recipe.cooking_time,
            })
        
        tfidf_matrix = self.vectorizer.fit_transform(recipe_texts)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(tfidf_matrix)
        
        clustered_recipes = {}
        for idx, cluster_id in enumerate(clusters):
            cluster_key = f'cluster_{cluster_id}'
            if cluster_key not in clustered_recipes:
                clustered_recipes[cluster_key] = []
            clustered_recipes[cluster_key].append(recipe_data[idx])
        
        return clustered_recipes
    
    def get_recipe_difficulty_prediction(self, recipe_id: int) -> Dict:
        """
        Предсказание сложности рецепта на основе параметров
        Простая модель классификации
        """
        try:
            recipe = Recipe.objects.prefetch_related('recipe_ingredients').get(id=recipe_id)
        except Recipe.DoesNotExist:
            return {'error': 'Recipe not found'}
        
        ingredients_count = recipe.recipe_ingredients.count()
        cooking_time = recipe.cooking_time
        
        difficulty_score = 0
        
        if cooking_time < 30:
            difficulty_score += 1
        elif cooking_time < 60:
            difficulty_score += 2
        else:
            difficulty_score += 3
        
        if ingredients_count < 5:
            difficulty_score += 1
        elif ingredients_count < 10:
            difficulty_score += 2
        else:
            difficulty_score += 3
        
        if difficulty_score <= 2:
            difficulty = 'Легкий'
        elif difficulty_score <= 4:
            difficulty = 'Средний'
        else:
            difficulty = 'Сложный'
        
        return {
            'recipe_id': recipe.id,
            'recipe_title': recipe.title,
            'difficulty': difficulty,
            'difficulty_score': difficulty_score,
            'factors': {
                'cooking_time': cooking_time,
                'ingredients_count': ingredients_count
            }
        }
    
    def recommend_for_cooking_time(self, max_time: int, top_n: int = 5) -> List[Dict]:
        """
        Рекомендовать рецепты в пределах заданного времени приготовления
        """
        recipes = Recipe.objects.filter(
            cooking_time__lte=max_time
        ).order_by('cooking_time')[:top_n]
        
        return [
            {
                'id': recipe.id,
                'title': recipe.title,
                'cooking_time': recipe.cooking_time,
                'servings': recipe.servings,
            }
            for recipe in recipes
        ]
    
    def analyze_ingredient_importance(self) -> List[Dict]:
        """
        Анализ важности ингредиентов в рецептах
        На основе частоты использования
        """
        ingredients = Ingredient.objects.annotate(
            usage_count=Count('recipe_ingredients')
        ).order_by('-usage_count')[:20]
        
        if not ingredients:
            return []
        
        max_count = ingredients[0].usage_count
        
        importance_data = []
        for ing in ingredients:
            importance_score = (ing.usage_count / max_count) * 100 if max_count > 0 else 0
            importance_data.append({
                'id': ing.id,
                'name': ing.name,
                'usage_count': ing.usage_count,
                'importance_score': round(importance_score, 2)
            })
        
        return importance_data
    
    def recommend_complementary_recipes(self, recipe_ids: List[int], top_n: int = 5) -> List[Dict]:
        """
        Рекомендовать дополняющие рецепты для списка покупок
        Находит рецепты с общими ингредиентами
        """
        if not recipe_ids:
            return []
        
        selected_recipes = Recipe.objects.filter(id__in=recipe_ids)
        
        ingredient_ids = set()
        for recipe in selected_recipes:
            recipe_ingredient_ids = recipe.recipe_ingredients.values_list('ingredient_id', flat=True)
            ingredient_ids.update(recipe_ingredient_ids)
        
        complementary_recipes = Recipe.objects.exclude(
            id__in=recipe_ids
        ).filter(
            recipe_ingredients__ingredient_id__in=ingredient_ids
        ).annotate(
            shared_ingredients=Count('recipe_ingredients')
        ).order_by('-shared_ingredients').distinct()[:top_n]
        
        recommendations = []
        for recipe in complementary_recipes:
            recommendations.append({
                'id': recipe.id,
                'title': recipe.title,
                'shared_ingredients': recipe.shared_ingredients,
                'cooking_time': recipe.cooking_time,
            })
        
        return recommendations

