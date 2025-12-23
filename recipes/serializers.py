"""
Сериализаторы для REST API
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Recipe, Ingredient, RecipeIngredient, ShoppingList


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента"""
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'unit']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента в рецепте"""
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = RecipeIngredient
        fields = ['id', 'ingredient', 'ingredient_id', 'quantity']


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта"""
    author = UserSerializer(read_only=True)
    recipe_ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    ingredients_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'description', 'instructions',
            'author', 'cooking_time', 'servings', 'source_url',
            'created_at', 'updated_at', 'recipe_ingredients',
            'ingredients_count'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']
    
    def get_ingredients_count(self, obj):
        return obj.recipe_ingredients.count()


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта"""
    class Meta:
        model = Recipe
        fields = [
            'title', 'description', 'instructions',
            'cooking_time', 'servings', 'source_url'
        ]


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок"""
    recipe = RecipeSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ShoppingList
        fields = ['id', 'user', 'recipe', 'added_at']
        read_only_fields = ['user', 'added_at']


class RecipeStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики рецептов"""
    total_recipes = serializers.IntegerField()
    total_ingredients = serializers.IntegerField()
    total_users = serializers.IntegerField()
    avg_cooking_time = serializers.FloatField()
    most_popular_recipes = RecipeSerializer(many=True)

