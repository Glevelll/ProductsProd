from django.urls import path
from . import views, analytics_views

urlpatterns = [
    path('', views.RecipeListView.as_view(), name='recipe_list'),
    path('recipe/<int:pk>/', views.RecipeDetailView.as_view(), name='recipe_detail'),
    path('recipe/create/', views.RecipeCreateView.as_view(), name='recipe_create'),
    path('recipe/<int:pk>/edit/', views.RecipeUpdateView.as_view(), name='recipe_update'),
    path('recipe/<int:pk>/delete/', views.RecipeDeleteView.as_view(), name='recipe_delete'),
    path('recipe/<int:pk>/add-ingredient/', views.add_ingredient_to_recipe, name='add_ingredient'),
    path('recipe/<int:recipe_pk>/remove-ingredient/<int:ingredient_pk>/', 
         views.remove_ingredient_from_recipe, name='remove_ingredient'),
    path('parse/', views.parse_recipe_view, name='parse_recipe'),
    path('shopping-list/', views.shopping_list_view, name='shopping_list'),
    path('shopping-list/add/<int:pk>/', views.add_to_shopping_list, name='add_to_shopping_list'),
    path('shopping-list/remove/<int:pk>/', views.remove_from_shopping_list, name='remove_from_shopping_list'),
    path('shopping-list/clear/', views.clear_shopping_list, name='clear_shopping_list'),
    
    # Analytics & ML
    path('analytics/', analytics_views.analytics_dashboard, name='analytics_dashboard'),
    path('statistics/', analytics_views.statistics_view, name='statistics'),
    path('statistics/dbapi/', analytics_views.dbapi_stats_view, name='dbapi_stats'),
    path('ml/recommendations/', analytics_views.ml_recommendations_view, name='ml_recommendations'),
    path('ml/recommendations/<int:recipe_id>/', analytics_views.ml_recommendations_view, name='ml_recommendations_recipe'),
    
    # Exports
    path('export/excel/', analytics_views.export_to_excel, name='export_excel'),
    path('export/csv/', analytics_views.export_to_csv, name='export_csv'),
    
    # ML API endpoints
    path('ml-api/similar/<int:recipe_id>/', analytics_views.api_ml_recommend_similar, name='api_ml_similar'),
    path('ml-api/by-ingredients/', analytics_views.api_ml_recommend_by_ingredients, name='api_ml_by_ingredients'),
    path('ml-api/clusters/', analytics_views.api_recipe_clusters, name='api_clusters'),
    path('dbapi/search/', analytics_views.api_dbapi_search, name='api_dbapi_search'),
]

