from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Recipe, Ingredient, RecipeIngredient, ShoppingList
from .services import RecipeParserService


class UserAuthenticationTests(TestCase):
    """Тесты регистрации и авторизации"""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')

    def test_user_registration(self):
        """Тест регистрации нового пользователя"""
        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_user_login(self):
        """Тест входа пользователя"""
        user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_user_logout(self):
        """Тест выхода пользователя"""
        user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)


class RecipeModelTests(TestCase):
    """Тесты модели рецепта"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )

    def test_create_recipe(self):
        """Тест создания рецепта"""
        recipe = Recipe.objects.create(
            title='Тестовый рецепт',
            description='Описание рецепта',
            instructions='Инструкции',
            author=self.user,
            cooking_time=30,
            servings=4
        )
        self.assertEqual(recipe.title, 'Тестовый рецепт')
        self.assertEqual(recipe.author, self.user)
        self.assertTrue(Recipe.objects.filter(title='Тестовый рецепт').exists())

    def test_recipe_string_representation(self):
        """Тест строкового представления рецепта"""
        recipe = Recipe.objects.create(
            title='Тестовый рецепт',
            description='Описание',
            instructions='Инструкции',
            author=self.user
        )
        self.assertEqual(str(recipe), 'Тестовый рецепт')


class IngredientModelTests(TestCase):
    """Тесты модели ингредиента"""

    def test_create_ingredient(self):
        """Тест создания ингредиента"""
        ingredient = Ingredient.objects.create(
            name='Мука',
            unit='г'
        )
        self.assertEqual(ingredient.name, 'Мука')
        self.assertEqual(ingredient.unit, 'г')

    def test_ingredient_string_representation(self):
        """Тест строкового представления ингредиента"""
        ingredient = Ingredient.objects.create(
            name='Сахар',
            unit='г'
        )
        self.assertEqual(str(ingredient), 'Сахар (г)')


class RecipeIngredientTests(TestCase):
    """Тесты связи рецепт-ингредиент"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.recipe = Recipe.objects.create(
            title='Тестовый рецепт',
            description='Описание',
            instructions='Инструкции',
            author=self.user
        )
        self.ingredient = Ingredient.objects.create(
            name='Мука',
            unit='г'
        )

    def test_add_ingredient_to_recipe(self):
        """Тест добавления ингредиента к рецепту"""
        recipe_ingredient = RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            quantity=500
        )
        self.assertEqual(recipe_ingredient.quantity, 500)
        self.assertEqual(self.recipe.ingredients.count(), 1)

    def test_recipe_ingredient_string_representation(self):
        """Тест строкового представления ингредиента в рецепте"""
        recipe_ingredient = RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            quantity=300
        )
        self.assertEqual(str(recipe_ingredient), 'Мука: 300 г')


class RecipeViewTests(TestCase):
    """Тесты представлений рецептов"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.recipe = Recipe.objects.create(
            title='Тестовый рецепт',
            description='Описание',
            instructions='Инструкции',
            author=self.user,
            cooking_time=30,
            servings=4
        )

    def test_recipe_list_view(self):
        """Тест списка рецептов"""
        response = self.client.get(reverse('recipe_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовый рецепт')

    def test_recipe_detail_view(self):
        """Тест детального просмотра рецепта"""
        response = self.client.get(
            reverse('recipe_detail', kwargs={'pk': self.recipe.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовый рецепт')

    def test_recipe_create_view_requires_login(self):
        """Тест создания рецепта требует авторизации"""
        response = self.client.get(reverse('recipe_create'))
        self.assertEqual(response.status_code, 302)

    def test_recipe_create_view_authenticated(self):
        """Тест создания рецепта авторизованным пользователем"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.post(reverse('recipe_create'), {
            'title': 'Новый рецепт',
            'description': 'Описание нового рецепта',
            'instructions': 'Инструкции приготовления',
            'cooking_time': 45,
            'servings': 2
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Recipe.objects.filter(title='Новый рецепт').exists())

    def test_recipe_update_view(self):
        """Тест обновления рецепта"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.post(
            reverse('recipe_update', kwargs={'pk': self.recipe.pk}),
            {
                'title': 'Обновленный рецепт',
                'description': 'Новое описание',
                'instructions': 'Новые инструкции',
                'cooking_time': 60,
                'servings': 6
            }
        )
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, 'Обновленный рецепт')

    def test_recipe_delete_view(self):
        """Тест удаления рецепта"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.post(
            reverse('recipe_delete', kwargs={'pk': self.recipe.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())


class ShoppingListTests(TestCase):
    """Тесты списка покупок"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.recipe = Recipe.objects.create(
            title='Тестовый рецепт',
            description='Описание',
            instructions='Инструкции',
            author=self.user
        )
        self.ingredient1 = Ingredient.objects.create(name='Мука', unit='г')
        self.ingredient2 = Ingredient.objects.create(name='Сахар', unit='г')
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient1,
            quantity=500
        )
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient2,
            quantity=200
        )

    def test_add_recipe_to_shopping_list(self):
        """Тест добавления рецепта в список покупок"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(
            reverse('add_to_shopping_list', kwargs={'pk': self.recipe.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ShoppingList.objects.filter(
                user=self.user,
                recipe=self.recipe
            ).exists()
        )

    def test_remove_recipe_from_shopping_list(self):
        """Тест удаления рецепта из списка покупок"""
        ShoppingList.objects.create(user=self.user, recipe=self.recipe)
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(
            reverse('remove_from_shopping_list', kwargs={'pk': self.recipe.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ShoppingList.objects.filter(
                user=self.user,
                recipe=self.recipe
            ).exists()
        )

    def test_shopping_list_view(self):
        """Тест просмотра списка покупок"""
        ShoppingList.objects.create(user=self.user, recipe=self.recipe)
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('shopping_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовый рецепт')

    def test_shopping_list_aggregation(self):
        """Тест агрегации ингредиентов в списке покупок"""
        recipe2 = Recipe.objects.create(
            title='Второй рецепт',
            description='Описание',
            instructions='Инструкции',
            author=self.user
        )
        RecipeIngredient.objects.create(
            recipe=recipe2,
            ingredient=self.ingredient1,
            quantity=300
        )
        
        ShoppingList.objects.create(user=self.user, recipe=self.recipe)
        ShoppingList.objects.create(user=self.user, recipe=recipe2)
        
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('shopping_list'))
        self.assertEqual(response.status_code, 200)

    def test_clear_shopping_list(self):
        """Тест очистки списка покупок"""
        ShoppingList.objects.create(user=self.user, recipe=self.recipe)
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('clear_shopping_list'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ShoppingList.objects.filter(user=self.user).count(), 0)


class RecipeParserServiceTests(TestCase):
    """Тесты сервиса парсинга рецептов"""

    def test_parser_initialization(self):
        """Тест инициализации парсера"""
        url = 'https://example.com/recipe'
        parser = RecipeParserService(url)
        self.assertEqual(parser.url, url)

    def test_normalize_unit(self):
        """Тест нормализации единиц измерения"""
        parser = RecipeParserService('https://example.com')
        self.assertEqual(parser._normalize_unit('гр'), 'г')
        self.assertEqual(parser._normalize_unit('грамм'), 'г')
        self.assertEqual(parser._normalize_unit('мл'), 'мл')
        self.assertEqual(parser._normalize_unit('шт'), 'шт')

    def test_parse_ingredient_string(self):
        """Тест парсинга строки ингредиента"""
        parser = RecipeParserService('https://example.com')
        
        result = parser._parse_ingredient_string('500 г муки')
        self.assertIsNotNone(result)
        self.assertEqual(result['quantity'], '500')
        self.assertEqual(result['unit'], 'г')
        
        result = parser._parse_ingredient_string('Соль - 1 ч.л.')
        self.assertIsNotNone(result)

    def test_extract_cooking_time_default(self):
        """Тест извлечения времени приготовления (по умолчанию)"""
        parser = RecipeParserService('https://example.com')
        parser.soup = None
        time = parser._extract_cooking_time()
        self.assertEqual(time, 30)

    def test_extract_servings_default(self):
        """Тест извлечения количества порций (по умолчанию)"""
        parser = RecipeParserService('https://example.com')
        parser.soup = None
        servings = parser._extract_servings()
        self.assertEqual(servings, 4)


class SearchTests(TestCase):
    """Тесты поиска рецептов"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        Recipe.objects.create(
            title='Шоколадный торт',
            description='Вкусный торт',
            instructions='Инструкции',
            author=self.user
        )
        Recipe.objects.create(
            title='Ванильное мороженое',
            description='Холодное лакомство',
            instructions='Инструкции',
            author=self.user
        )

    def test_search_recipes(self):
        """Тест поиска рецептов"""
        response = self.client.get(reverse('recipe_list'), {'search': 'шоколад'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Шоколадный торт')
        self.assertNotContains(response, 'Ванильное мороженое')

    def test_search_no_results(self):
        """Тест поиска без результатов"""
        response = self.client.get(reverse('recipe_list'), {'search': 'несуществующий'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Шоколадный торт')

