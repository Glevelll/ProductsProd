from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Ingredient(models.Model):
    """Модель ингредиента"""
    name = models.CharField(max_length=200, unique=True, verbose_name='Название')
    unit = models.CharField(max_length=50, default='г', verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.unit})"


class Recipe(models.Model):
    """Модель рецепта"""
    title = models.CharField(max_length=300, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    instructions = models.TextField(verbose_name='Инструкции')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    cooking_time = models.PositiveIntegerField(
        default=30,
        verbose_name='Время приготовления (мин)'
    )
    servings = models.PositiveIntegerField(default=4, verbose_name='Порций')
    source_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Источник (URL)'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('recipe_detail', kwargs={'pk': self.pk})


class RecipeIngredient(models.Model):
    """Связь рецепт-ингредиент с количеством"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        unique_together = [['recipe', 'ingredient']]

    def __str__(self):
        return f"{self.ingredient.name}: {self.quantity} {self.ingredient.unit}"


class ShoppingList(models.Model):
    """Модель списка покупок"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_lists',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_lists',
        verbose_name='Рецепт'
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        unique_together = [['user', 'recipe']]
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.recipe.title}"

