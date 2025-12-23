from django import forms
from .models import Recipe, RecipeIngredient, Ingredient


class RecipeForm(forms.ModelForm):
    """Форма создания/редактирования рецепта"""

    class Meta:
        model = Recipe
        fields = ['title', 'description', 'instructions', 'cooking_time', 'servings', 'source_url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название рецепта'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Краткое описание'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Пошаговая инструкция приготовления'
            }),
            'cooking_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'servings': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'source_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/recipe'
            }),
        }


class RecipeIngredientForm(forms.ModelForm):
    """Форма добавления ингредиента к рецепту"""

    ingredient_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Название ингредиента'
        }),
        label='Ингредиент'
    )

    unit = forms.CharField(
        max_length=50,
        required=True,
        initial='г',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'г, мл, шт'
        }),
        label='Единица измерения'
    )

    class Meta:
        model = RecipeIngredient
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.01,
                'step': 0.01,
                'placeholder': 'Количество'
            }),
        }

    def save(self, recipe, commit=True):
        ingredient_name = self.cleaned_data['ingredient_name']
        unit = self.cleaned_data['unit']
        quantity = self.cleaned_data['quantity']

        ingredient, created = Ingredient.objects.get_or_create(
            name=ingredient_name,
            defaults={'unit': unit}
        )

        recipe_ingredient, created = RecipeIngredient.objects.get_or_create(
            recipe=recipe,
            ingredient=ingredient,
            defaults={'quantity': quantity}
        )

        if not created:
            recipe_ingredient.quantity = quantity
            if commit:
                recipe_ingredient.save()

        return recipe_ingredient


class ParseRecipeForm(forms.Form):
    """Форма для парсинга рецепта по URL"""
    url = forms.URLField(
        required=True,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.com/recipe/my-recipe'
        }),
        label='URL рецепта'
    )

