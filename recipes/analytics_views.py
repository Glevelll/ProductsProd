"""
Views для аналитики и работы с новыми технологиями
dbAPI, pandas, scikit-learn, matplotlib, seaborn
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from .db_service import DatabaseService, get_recipe_stats_via_dbapi, get_top_ingredients_via_dbapi
from .pandas_service import PandasDataService
from .ml_service import RecipeRecommendationService
from .visualization_service import VisualizationService
from .models import Recipe
from typing import Dict


@login_required
def analytics_dashboard(request):
    """
    Главная страница аналитики с визуализациями
    Использует matplotlib и seaborn
    """
    viz_service = VisualizationService()
    visualizations = viz_service.generate_all_visualizations()
    
    context = {
        'visualizations': visualizations,
        'title': 'Аналитика рецептов'
    }
    return render(request, 'recipes/analytics_dashboard.html', context)


@login_required
def statistics_view(request):
    """
    Статистика через pandas
    """
    pandas_service = PandasDataService()
    
    recipe_stats = pandas_service.get_recipe_statistics()
    ingredient_analysis = pandas_service.get_ingredient_analysis()
    cooking_time_dist = pandas_service.get_cooking_time_distribution()
    correlation = pandas_service.correlation_analysis()
    
    if request.user.id:
        user_shopping_analysis = pandas_service.get_user_shopping_analysis(request.user.id)
    else:
        user_shopping_analysis = {}
    
    context = {
        'recipe_stats': recipe_stats,
        'ingredient_analysis': ingredient_analysis,
        'cooking_time_dist': cooking_time_dist,
        'correlation': correlation,
        'user_shopping_analysis': user_shopping_analysis,
        'title': 'Статистика (Pandas)'
    }
    return render(request, 'recipes/statistics.html', context)


@login_required
def dbapi_stats_view(request):
    """
    Статистика через прямые SQL запросы (dbAPI)
    """
    with DatabaseService() as db:
        recipe_stats = db.get_recipe_stats_raw()
        top_ingredients = db.get_top_ingredients_raw(15)
        user_stats = db.get_user_recipe_stats_raw(request.user.id)
        shopping_summary = db.get_shopping_list_summary_raw(request.user.id)
    
    context = {
        'recipe_stats': recipe_stats,
        'top_ingredients': top_ingredients,
        'user_stats': user_stats,
        'shopping_summary': shopping_summary,
        'title': 'Статистика (dbAPI)'
    }
    return render(request, 'recipes/dbapi_stats.html', context)


@login_required
def ml_recommendations_view(request, recipe_id=None):
    """
    Рекомендации рецептов через ML (scikit-learn)
    """
    ml_service = RecipeRecommendationService()
    
    similar_recipes = []
    difficulty_prediction = {}
    quick_recipes = []
    ingredient_importance = []
    
    if recipe_id:
        similar_recipes = ml_service.recommend_similar_recipes(recipe_id, top_n=5)
        difficulty_prediction = ml_service.get_recipe_difficulty_prediction(recipe_id)
        current_recipe = get_object_or_404(Recipe, id=recipe_id)
    else:
        current_recipe = None
    
    quick_recipes = ml_service.recommend_for_cooking_time(max_time=30, top_n=10)
    ingredient_importance = ml_service.analyze_ingredient_importance()
    
    context = {
        'current_recipe': current_recipe,
        'similar_recipes': similar_recipes,
        'difficulty_prediction': difficulty_prediction,
        'quick_recipes': quick_recipes,
        'ingredient_importance': ingredient_importance,
        'title': 'ML Рекомендации'
    }
    return render(request, 'recipes/ml_recommendations.html', context)


@login_required
def export_to_excel(request):
    """
    Экспорт данных в Excel через pandas
    """
    pandas_service = PandasDataService()
    excel_file = pandas_service.export_recipes_to_excel()
    
    response = HttpResponse(
        excel_file,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="recipes_export.xlsx"'
    
    return response


@login_required
def export_to_csv(request):
    """
    Экспорт данных в CSV через pandas
    """
    pandas_service = PandasDataService()
    csv_data = pandas_service.export_recipes_to_csv()
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="recipes_export.csv"'
    
    return response


@require_http_methods(['GET'])
@login_required
def api_ml_recommend_similar(request, recipe_id):
    """
    API endpoint для получения похожих рецептов через ML
    """
    ml_service = RecipeRecommendationService()
    recommendations = ml_service.recommend_similar_recipes(recipe_id, top_n=5)
    
    return JsonResponse({
        'recipe_id': recipe_id,
        'recommendations': recommendations
    })


@require_http_methods(['POST'])
@login_required
def api_ml_recommend_by_ingredients(request):
    """
    API endpoint для рекомендаций по ингредиентам
    """
    import json
    data = json.loads(request.body)
    ingredient_ids = data.get('ingredient_ids', [])
    
    ml_service = RecipeRecommendationService()
    recommendations = ml_service.recommend_by_ingredients(ingredient_ids, top_n=10)
    
    return JsonResponse({
        'ingredient_ids': ingredient_ids,
        'recommendations': recommendations
    })


@require_http_methods(['GET'])
@login_required
def api_recipe_clusters(request):
    """
    API endpoint для кластеризации рецептов
    """
    n_clusters = int(request.GET.get('n_clusters', 5))
    
    ml_service = RecipeRecommendationService()
    clusters = ml_service.cluster_recipes(n_clusters=n_clusters)
    
    return JsonResponse({
        'n_clusters': n_clusters,
        'clusters': clusters
    })


@require_http_methods(['GET'])
@login_required
def api_dbapi_search(request):
    """
    API endpoint для поиска через dbAPI
    """
    search_term = request.GET.get('q', '')
    
    if not search_term:
        return JsonResponse({'error': 'Search term required'}, status=400)
    
    with DatabaseService() as db:
        results = db.search_recipes_raw(search_term)
    
    return JsonResponse({
        'search_term': search_term,
        'results': results
    })

