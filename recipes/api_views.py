"""
REST API Views
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.contrib.auth.models import User
from django.db.models import Count, Avg
from .models import Recipe, Ingredient, RecipeIngredient, ShoppingList
from .serializers import (
    RecipeSerializer, RecipeCreateSerializer, IngredientSerializer,
    ShoppingListSerializer, UserSerializer, RecipeStatsSerializer
)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    API endpoint для рецептов
    
    list: GET /api/recipes/ - список всех рецептов
    retrieve: GET /api/recipes/{id}/ - детали рецепта
    create: POST /api/recipes/ - создать рецепт
    update: PUT /api/recipes/{id}/ - обновить рецепт
    partial_update: PATCH /api/recipes/{id}/ - частичное обновление
    destroy: DELETE /api/recipes/{id}/ - удалить рецепт
    """
    queryset = Recipe.objects.all().select_related('author').prefetch_related('recipe_ingredients')
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'instructions']
    ordering_fields = ['created_at', 'cooking_time', 'servings']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_to_shopping_list(self, request, pk=None):
        """Добавить рецепт в список покупок"""
        recipe = self.get_object()
        shopping_item, created = ShoppingList.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if created:
            return Response(
                {'status': 'added', 'message': 'Рецепт добавлен в список покупок'},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'status': 'exists', 'message': 'Рецепт уже в списке покупок'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def remove_from_shopping_list(self, request, pk=None):
        """Удалить рецепт из списка покупок"""
        recipe = self.get_object()
        deleted, _ = ShoppingList.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if deleted:
            return Response(
                {'status': 'removed', 'message': 'Рецепт удален из списка покупок'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'status': 'not_found', 'message': 'Рецепт не найден в списке покупок'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Статистика по рецептам"""
        total_recipes = Recipe.objects.count()
        total_ingredients = Ingredient.objects.count()
        total_users = User.objects.filter(recipes__isnull=False).distinct().count()
        avg_cooking_time = Recipe.objects.aggregate(Avg('cooking_time'))['cooking_time__avg']
        
        most_popular = Recipe.objects.annotate(
            shopping_count=Count('in_shopping_lists')
        ).order_by('-shopping_count')[:5]
        
        data = {
            'total_recipes': total_recipes,
            'total_ingredients': total_ingredients,
            'total_users': total_users,
            'avg_cooking_time': round(avg_cooking_time, 2) if avg_cooking_time else 0,
            'most_popular_recipes': RecipeSerializer(most_popular, many=True).data
        }
        
        return Response(data)


class IngredientViewSet(viewsets.ModelViewSet):
    """
    API endpoint для ингредиентов
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ShoppingListViewSet(viewsets.ModelViewSet):
    """
    API endpoint для списка покупок
    """
    serializer_class = ShoppingListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ShoppingList.objects.filter(user=self.request.user).select_related('recipe')
    
    @action(detail=False, methods=['get'])
    def aggregated(self, request):
        """Агрегированный список ингредиентов для покупки"""
        shopping_items = self.get_queryset()
        
        ingredient_totals = {}
        
        for item in shopping_items:
            recipe_ingredients = item.recipe.recipe_ingredients.select_related('ingredient')
            for ri in recipe_ingredients:
                key = (ri.ingredient.name, ri.ingredient.unit)
                if key in ingredient_totals:
                    ingredient_totals[key] += float(ri.quantity)
                else:
                    ingredient_totals[key] = float(ri.quantity)
        
        shopping_list = [
            {
                'name': name,
                'quantity': round(quantity, 2),
                'unit': unit
            }
            for (name, unit), quantity in sorted(ingredient_totals.items())
        ]
        
        return Response({
            'recipes': ShoppingListSerializer(shopping_items, many=True).data,
            'ingredients': shopping_list
        })
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Очистить список покупок"""
        deleted_count, _ = self.get_queryset().delete()
        return Response(
            {'status': 'cleared', 'deleted': deleted_count},
            status=status.HTTP_204_NO_CONTENT
        )


@api_view(['GET'])
def api_root(request):
    """
    REST API корневой endpoint
    """
    return Response({
        'message': 'Recipe Management API',
        'version': '1.0',
        'endpoints': {
            'recipes': '/api/recipes/',
            'ingredients': '/api/ingredients/',
            'shopping_list': '/api/shopping-list/',
            'recipe_stats': '/api/recipes/stats/',
        }
    })

