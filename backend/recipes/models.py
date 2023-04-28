from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

User = get_user_model()


class Tags(models.Model):
    """Инициализация модели Tags."""

    name = models.CharField(
        'Название',
        unique=True,
        max_length=200
        )
    color = models.CharField(
        'HEX-цвет',
        null=True,
        max_length=7,
        validators=[
            RegexValidator(
                '^#([a-fA-F0-9]{6})',
                message='Введите HEX-код цвета.'
            )
        ]
    )
    slug = models.SlugField(max_length=15, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredients(models.Model):
    """Инициализация модели Ingredients."""

    name = models.CharField('Название', max_length=200)
    measurement_unit = models.CharField('Ед.изм.', max_length=10)

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Инициализация модели Recipes."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        blank=False,
        verbose_name='Автор',
    )
    name = models.CharField(
        'Название',
        max_length=200
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
        help_text='Загрузите картинку',
        blank=False,
    )
    cooking_time = models.IntegerField(
        default=1,
        verbose_name='Время приготовления(мин.)',
        validators=[
            MinValueValidator(1),
        ],
    )
    text = models.TextField(
        'Описание рецепта',
        blank=False,
    )
    tags = models.ManyToManyField(
        Tags,
        through='TagRecipe',
        blank=False,
        related_name='recipes',
        verbose_name='Теги',
    )
    ingredient = models.ManyToManyField(
        Ingredients,
        through='IngredientRecipe',
        blank=False,
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    pub_date = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class TagRecipe(models.Model):
    """Инициализация модели TagReceipe."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    tag = models.ForeignKey(
        Tags,
        on_delete=models.CASCADE,
        related_name='recipe_tags',
        verbose_name='Тег',
    )

    class Meta:
        ordering = ['-tag']
        verbose_name = 'Связь тег-рецепт'
        verbose_name_plural = 'Связи тег-рецепт'
        constraints = [models.UniqueConstraint(
            fields=['recipe', 'tag'],
            name='unique_tagrecipe',
            ),
        ]

    def __str__(self):
        return f'{self.tag} {self.recipe}'


class IngredientRecipe(models.Model):
    """Инициализация модели TagReceipe."""

    amount = models.IntegerField(
        'Количество',
        default=1,
        validators=[
            MinValueValidator(1),
        ],
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='ingredients'
    )
    ingredients = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        related_name='recipe',
    )

    class Meta:
        ordering = ['-ingredients']
        verbose_name = 'Ингредиент-рецепт'
        verbose_name_plural = 'Ингредиент-рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredients'], name='unique_ingredient'
            ),
        ]

    def __str__(self):
        return f'{self.ingredients} {self.recipe}'


class FavoriteRecipe(models.Model):
    """Инициализация модели FavoriteRecipe."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipe_user',
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Избранный рецепт',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite_recipe'
            ),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShoppingCart(models.Model):
    """Инициализация модели ShoppingCart."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_user',
        verbose_name='Пользователь корзины',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_in_cart',
        verbose_name='Рецепт в корзине',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_user_recipe'
            ),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'
