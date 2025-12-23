from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum
from .models import Recipe, Ingredient, RecipeIngredient, ShoppingList
from .forms import RecipeForm, RecipeIngredientForm, ParseRecipeForm
from .services import RecipeParserService


class RecipeListView(ListView):
    """Список всех рецептов"""
    model = Recipe
    template_name = 'recipes/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 12

    def get_queryset(self):
        queryset = Recipe.objects.select_related('author').prefetch_related('ingredients')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class RecipeDetailView(DetailView):
    """Детальный просмотр рецепта"""
    model = Recipe
    template_name = 'recipes/recipe_detail.html'
    context_object_name = 'recipe'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        context['recipe_ingredients'] = recipe.recipe_ingredients.select_related('ingredient')
        
        if self.request.user.is_authenticated:
            context['in_shopping_list'] = ShoppingList.objects.filter(
                user=self.request.user,
                recipe=recipe
            ).exists()
        else:
            context['in_shopping_list'] = False
            
        return context


class RecipeCreateView(LoginRequiredMixin, CreateView):
    """Создание нового рецепта"""
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'
    success_url = reverse_lazy('recipe_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Рецепт успешно создан!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создать рецепт'
        context['button_text'] = 'Создать'
        return context


class RecipeUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование рецепта"""
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'

    def get_queryset(self):
        return Recipe.objects.filter(author=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Рецепт успешно обновлен!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактировать рецепт'
        context['button_text'] = 'Сохранить'
        context['recipe'] = self.get_object()
        return context


class RecipeDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление рецепта"""
    model = Recipe
    template_name = 'recipes/recipe_confirm_delete.html'
    success_url = reverse_lazy('recipe_list')

    def get_queryset(self):
        return Recipe.objects.filter(author=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Рецепт успешно удален!')
        return super().delete(request, *args, **kwargs)


@login_required
def add_ingredient_to_recipe(request, pk):
    """Добавление ингредиента к рецепту"""
    recipe = get_object_or_404(Recipe, pk=pk, author=request.user)

    if request.method == 'POST':
        form = RecipeIngredientForm(request.POST)
        if form.is_valid():
            form.save(recipe=recipe)
            messages.success(request, 'Ингредиент добавлен!')
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeIngredientForm()

    context = {
        'form': form,
        'recipe': recipe,
    }
    return render(request, 'recipes/add_ingredient.html', context)


@login_required
def remove_ingredient_from_recipe(request, recipe_pk, ingredient_pk):
    """Удаление ингредиента из рецепта"""
    recipe = get_object_or_404(Recipe, pk=recipe_pk, author=request.user)
    recipe_ingredient = get_object_or_404(
        RecipeIngredient,
        recipe=recipe,
        ingredient_id=ingredient_pk
    )
    recipe_ingredient.delete()
    messages.success(request, 'Ингредиент удален!')
    return redirect('recipe_detail', pk=recipe.pk)


@login_required
def parse_recipe_view(request):
    """Парсинг рецепта с внешнего сайта"""
    if request.method == 'POST':
        form = ParseRecipeForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            parser = RecipeParserService(url)
            recipe_data = parser.parse_recipe()

            if recipe_data:
                recipe = Recipe.objects.create(
                    title=recipe_data['title'],
                    description=recipe_data['description'],
                    instructions=recipe_data['instructions'],
                    author=request.user,
                    cooking_time=recipe_data['cooking_time'],
                    servings=recipe_data['servings'],
                    source_url=url
                )

                for ing_data in recipe_data['ingredients']:
                    ingredient, created = Ingredient.objects.get_or_create(
                        name=ing_data['name'],
                        defaults={'unit': ing_data['unit']}
                    )
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient,
                        quantity=ing_data['quantity']
                    )

                messages.success(request, f'Рецепт "{recipe.title}" успешно импортирован!')
                return redirect('recipe_detail', pk=recipe.pk)
            else:
                messages.error(request, 'Не удалось распарсить рецепт. Проверьте URL.')
    else:
        form = ParseRecipeForm()

    context = {
        'form': form,
        'title': 'Импорт рецепта'
    }
    return render(request, 'recipes/parse_recipe.html', context)


@login_required
def add_to_shopping_list(request, pk):
    """Добавить рецепт в список покупок"""
    recipe = get_object_or_404(Recipe, pk=pk)
    ShoppingList.objects.get_or_create(user=request.user, recipe=recipe)
    messages.success(request, f'Рецепт "{recipe.title}" добавлен в список покупок!')
    return redirect('recipe_detail', pk=pk)


@login_required
def remove_from_shopping_list(request, pk):
    """Удалить рецепт из списка покупок"""
    recipe = get_object_or_404(Recipe, pk=pk)
    ShoppingList.objects.filter(user=request.user, recipe=recipe).delete()
    messages.success(request, f'Рецепт "{recipe.title}" удален из списка покупок!')
    return redirect('recipe_detail', pk=pk)


@login_required
def shopping_list_view(request):
    """Просмотр списка покупок"""
    shopping_items = ShoppingList.objects.filter(user=request.user).select_related('recipe')
    
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
    
    context = {
        'shopping_items': shopping_items,
        'shopping_list': shopping_list,
    }
    return render(request, 'recipes/shopping_list.html', context)


@login_required
def clear_shopping_list(request):
    """Очистить список покупок"""
    ShoppingList.objects.filter(user=request.user).delete()
    messages.success(request, 'Список покупок очищен!')
    return redirect('shopping_list')

