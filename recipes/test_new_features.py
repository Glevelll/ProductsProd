"""
Тесты для новых функций: REST API, dbAPI, pandas, ML, визуализация
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Recipe, Ingredient, RecipeIngredient
from .db_service import DatabaseService, get_recipe_stats_via_dbapi
from .pandas_service import PandasDataService
from .ml_service import RecipeRecommendationService
from .visualization_service import VisualizationService
import json


class RESTAPITests(TestCase):
    """Тесты REST API (webAPI)"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)
        
        self.recipe = Recipe.objects.create(
            title='Test Recipe API',
            description='API Test Description',
            instructions='API Test Instructions',
            author=self.user,
            cooking_time=30,
            servings=4
        )

    def test_api_recipe_list(self):
        """Тест получения списка рецептов через API"""
        response = self.client.get('/api/recipes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_api_recipe_detail(self):
        """Тест получения деталей рецепта через API"""
        response = self.client.get(f'/api/recipes/{self.recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Recipe API')

    def test_api_recipe_create(self):
        """Тест создания рецепта через API"""
        data = {
            'title': 'New API Recipe',
            'description': 'Created via API',
            'instructions': 'API Instructions',
            'cooking_time': 45,
            'servings': 2
        }
        response = self.client.post('/api/recipes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Recipe.objects.filter(title='New API Recipe').exists())

    def test_api_recipe_stats(self):
        """Тест получения статистики через API"""
        response = self.client.get('/api/recipes/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_recipes', response.data)
        self.assertIn('avg_cooking_time', response.data)

    def test_api_add_to_shopping_list(self):
        """Тест добавления в список покупок через API"""
        response = self.client.post(f'/api/recipes/{self.recipe.id}/add_to_shopping_list/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class dbAPITests(TestCase):
    """Тесты dbAPI (прямые SQL запросы)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        for i in range(5):
            Recipe.objects.create(
                title=f'Recipe {i}',
                description='Description',
                instructions='Instructions',
                author=self.user,
                cooking_time=30 + i * 10,
                servings=4
            )

    def test_dbapi_connection(self):
        """Тест подключения к БД через dbAPI"""
        with DatabaseService() as db:
            self.assertIsNotNone(db.connection)
            self.assertIsNotNone(db.cursor)

    def test_dbapi_recipe_stats(self):
        """Тест получения статистики через SQL"""
        stats = get_recipe_stats_via_dbapi()
        self.assertIn('total_recipes', stats)
        self.assertEqual(stats['total_recipes'], 5)
        self.assertGreater(stats['avg_cooking_time'], 0)

    def test_dbapi_search(self):
        """Тест поиска через SQL"""
        with DatabaseService() as db:
            results = db.search_recipes_raw('Recipe 1')
            self.assertIsInstance(results, list)

    def test_dbapi_user_stats(self):
        """Тест статистики пользователя через SQL"""
        with DatabaseService() as db:
            stats = db.get_user_recipe_stats_raw(self.user.id)
            self.assertEqual(stats['total_recipes'], 5)


class PandasTests(TestCase):
    """Тесты pandas (анализ данных)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        for i in range(10):
            Recipe.objects.create(
                title=f'Recipe {i}',
                description='Description',
                instructions='Instructions',
                author=self.user,
                cooking_time=20 + i * 5,
                servings=2 + i
            )

    def test_pandas_recipes_to_dataframe(self):
        """Тест конвертации рецептов в DataFrame"""
        df = PandasDataService.recipes_to_dataframe()
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 10)
        self.assertIn('title', df.columns)
        self.assertIn('cooking_time', df.columns)

    def test_pandas_statistics(self):
        """Тест получения статистики через pandas"""
        stats = PandasDataService.get_recipe_statistics()
        self.assertEqual(stats['total_recipes'], 10)
        self.assertIn('statistics', stats)
        self.assertIn('cooking_time', stats['statistics'])

    def test_pandas_export_csv(self):
        """Тест экспорта в CSV"""
        csv_data = PandasDataService.export_recipes_to_csv()
        self.assertIsInstance(csv_data, str)
        self.assertIn('title', csv_data)

    def test_pandas_export_excel(self):
        """Тест экспорта в Excel"""
        excel_file = PandasDataService.export_recipes_to_excel()
        self.assertIsNotNone(excel_file)

    def test_pandas_correlation_analysis(self):
        """Тест корреляционного анализа"""
        correlation = PandasDataService.correlation_analysis()
        self.assertIsInstance(correlation, dict)


class MLTests(TestCase):
    """Тесты scikit-learn (машинное обучение)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
        self.ingredient1 = Ingredient.objects.create(name='Мука', unit='г')
        self.ingredient2 = Ingredient.objects.create(name='Сахар', unit='г')
        
        for i in range(5):
            recipe = Recipe.objects.create(
                title=f'Рецепт {i}',
                description=f'Описание рецепта {i}',
                instructions='Инструкции',
                author=self.user,
                cooking_time=30 + i * 10,
                servings=4
            )
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=self.ingredient1,
                quantity=100 + i * 50
            )

    def test_ml_similar_recipes(self):
        """Тест рекомендации похожих рецептов через ML"""
        ml_service = RecipeRecommendationService()
        recipe = Recipe.objects.first()
        recommendations = ml_service.recommend_similar_recipes(recipe.id, top_n=3)
        self.assertIsInstance(recommendations, list)

    def test_ml_difficulty_prediction(self):
        """Тест предсказания сложности рецепта"""
        ml_service = RecipeRecommendationService()
        recipe = Recipe.objects.first()
        prediction = ml_service.get_recipe_difficulty_prediction(recipe.id)
        self.assertIn('difficulty', prediction)
        self.assertIn(prediction['difficulty'], ['Легкий', 'Средний', 'Сложный'])

    def test_ml_recommend_by_ingredients(self):
        """Тест рекомендаций по ингредиентам"""
        ml_service = RecipeRecommendationService()
        recommendations = ml_service.recommend_by_ingredients([self.ingredient1.id], top_n=3)
        self.assertIsInstance(recommendations, list)

    def test_ml_quick_recipes(self):
        """Тест рекомендации быстрых рецептов"""
        ml_service = RecipeRecommendationService()
        quick = ml_service.recommend_for_cooking_time(max_time=40, top_n=5)
        self.assertIsInstance(quick, list)
        for recipe in quick:
            self.assertLessEqual(recipe['cooking_time'], 40)

    def test_ml_ingredient_importance(self):
        """Тест анализа важности ингредиентов"""
        ml_service = RecipeRecommendationService()
        importance = ml_service.analyze_ingredient_importance()
        self.assertIsInstance(importance, list)

    def test_ml_clustering(self):
        """Тест кластеризации рецептов"""
        ml_service = RecipeRecommendationService()
        clusters = ml_service.cluster_recipes(n_clusters=2)
        self.assertIsInstance(clusters, dict)


class VisualizationTests(TestCase):
    """Тесты matplotlib и seaborn (визуализация)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        for i in range(10):
            Recipe.objects.create(
                title=f'Recipe {i}',
                description='Description',
                instructions='Instructions',
                author=self.user,
                cooking_time=20 + i * 5,
                servings=2 + (i % 4)
            )

    def test_visualization_cooking_time_distribution(self):
        """Тест создания графика распределения времени"""
        viz_service = VisualizationService()
        plot = viz_service.plot_cooking_time_distribution()
        self.assertIsInstance(plot, str)
        if plot:
            self.assertTrue(len(plot) > 0)

    def test_visualization_servings_distribution(self):
        """Тест создания графика распределения порций"""
        viz_service = VisualizationService()
        plot = viz_service.plot_servings_distribution()
        self.assertIsInstance(plot, str)

    def test_visualization_generate_all(self):
        """Тест генерации всех визуализаций"""
        viz_service = VisualizationService()
        visualizations = viz_service.generate_all_visualizations()
        self.assertIsInstance(visualizations, dict)
        self.assertIn('cooking_time_distribution', visualizations)


class IntegrationTests(TestCase):
    """Интеграционные тесты для всех новых функций"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.client.login(username='testuser', password='TestPass123!')
        
        for i in range(5):
            Recipe.objects.create(
                title=f'Recipe {i}',
                description='Description',
                instructions='Instructions',
                author=self.user,
                cooking_time=30,
                servings=4
            )

    def test_analytics_dashboard_view(self):
        """Тест страницы аналитики"""
        response = self.client.get(reverse('analytics_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('visualizations', response.context)

    def test_statistics_view(self):
        """Тест страницы статистики pandas"""
        response = self.client.get(reverse('statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('recipe_stats', response.context)

    def test_dbapi_stats_view(self):
        """Тест страницы статистики dbAPI"""
        response = self.client.get(reverse('dbapi_stats'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('recipe_stats', response.context)

    def test_ml_recommendations_view(self):
        """Тест страницы ML рекомендаций"""
        response = self.client.get(reverse('ml_recommendations'))
        self.assertEqual(response.status_code, 200)

    def test_export_excel(self):
        """Тест экспорта в Excel"""
        response = self.client.get(reverse('export_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_export_csv(self):
        """Тест экспорта в CSV"""
        response = self.client.get(reverse('export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

