from django.contrib import admin
from .models import Recipe, Ingredient, RecipeIngredient, ShoppingList


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для ингредиентов в рецепте"""
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ['ingredient']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов"""
    list_display = ['title', 'author', 'cooking_time', 'servings', 'created_at']
    list_filter = ['created_at', 'cooking_time']
    search_fields = ['title', 'description', 'author__username']
    date_hierarchy = 'created_at'
    inlines = [RecipeIngredientInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'author', 'description')
        }),
        ('Приготовление', {
            'fields': ('instructions', 'cooking_time', 'servings')
        }),
        ('Дополнительно', {
            'fields': ('source_url', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов"""
    list_display = ['name', 'unit']
    search_fields = ['name']
    ordering = ['name']


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админка для связи рецепт-ингредиент"""
    list_display = ['recipe', 'ingredient', 'quantity']
    list_filter = ['recipe', 'ingredient']
    search_fields = ['recipe__title', 'ingredient__name']
    autocomplete_fields = ['recipe', 'ingredient']


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    """Админка для списка покупок"""
    list_display = ['user', 'recipe', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'recipe__title']
    date_hierarchy = 'added_at'

