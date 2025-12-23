"""
URL configuration для REST API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import RecipeViewSet, IngredientViewSet, ShoppingListViewSet, api_root

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='api-recipe')
router.register(r'ingredients', IngredientViewSet, basename='api-ingredient')
router.register(r'shopping-list', ShoppingListViewSet, basename='api-shopping-list')

urlpatterns = [
    path('', api_root, name='api-root'),
    path('', include(router.urls)),
]

