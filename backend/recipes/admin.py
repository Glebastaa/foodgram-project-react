from django.contrib import admin

from recipes.models import (FavoriteRecipe, IngredientRecipe, Ingredients,
                            Recipe, ShoppingCart, TagRecipe, Tags, User)
from users.models import Follow


if not hasattr(admin, "display"):
    def display(description):
        def decorator(fn):
            fn.short_description = description
            return fn
        return decorator
    setattr(admin, "display", display)


@admin.register(Recipe)
class RecipesAdmin(admin.ModelAdmin):
    """Настройка параметров отображения рецептов в админке"""

    list_display = (
        'pk',
        'name',
        'author',
        'in_favorites',
        'cooking_time',
        'text',
        'image'
    )
    list_editable = (
        'name', 'cooking_time', 'text',
        'image', 'author',
    )
    readonly_fields = ('in_favorites',)
    list_filter = ('name', 'author', 'tags')
    empty_value_display = '-пусто-'

    @admin.display(description='В избранном')
    def in_favorites(self, obj):
        return obj.favorite_recipe.count()


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    """Настройка параметров отображения ингредиентов в админке"""

    list_display = (
        "pk",
        "name",
        "measurement_unit",
    )
    list_editable = ("name", "measurement_unit")
    search_fields = ("name",)
    empty_value_display = "-пусто-"


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    """Настройка параметров отображения тэгов в админке"""

    list_display = (
        "pk",
        "name",
        "color",
        "slug",
    )
    search_fields = (
        "name",
        "slug",
    )
    empty_value_display = "-пусто-"


@admin.register(TagRecipe)
class TagRecipeAdmin(admin.ModelAdmin):
    """Настройка параметров отображения
    свяски тэг-рецепт в админке"""

    list_display = (
        "pk",
        "recipe",
        "tag",
    )
    empty_value_display = "-пусто-"


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    """Настройка параметров отображения
    свяски ингредиент-рецепт в админке"""

    list_display = (
        "pk",
        "recipe",
        "ingredients",
    )
    empty_value_display = "-пусто-"


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Настройка параметров отображения пользователей в админке"""

    list_display = (
        'username', 'pk', 'email', 'password', 'first_name', 'last_name',
    )
    list_editable = ('password', )
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    empty_value_display = '-пусто-'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Настройка параметров отображения подписок в админке"""

    list_display = ('pk', 'user', 'author')
    list_editable = ('user', 'author')
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCart(admin.ModelAdmin):
    """Настройка параметров отображения корзины в админке"""

    all_fields = [f.name for f in ShoppingCart._meta.fields]
    parent_fields = ShoppingCart.get_deferred_fields(ShoppingCart)
    list_display = all_fields
    read_only = parent_fields
    empty_value_display = "-пусто-"


@admin.register(FavoriteRecipe)
class FavoriteRecipe(admin.ModelAdmin):
    """Настройка параметров отображения избранных рецептов в админке"""

    all_fields = [f.name for f in FavoriteRecipe._meta.fields]
    parent_fields = FavoriteRecipe.get_deferred_fields(FavoriteRecipe)
    list_display = all_fields
    read_only = parent_fields
    empty_value_display = "-пусто-"
