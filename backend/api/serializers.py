from djoser.serializers import (
    TokenCreateSerializer,
    UserCreateSerializer, UserSerializer,
)
from drf_base64.fields import Base64ImageField
from rest_framework.exceptions import NotFound
from rest_framework import serializers
from django.db import transaction

from .mixins import RecipeFieldsMixin
from recipes.models import (FavoriteRecipe, IngredientRecipe, Ingredients,
                            Recipe, ShoppingCart, Tags, User)
from users.models import Follow


class UserRegistrationSerializer(UserCreateSerializer):
    """Сериализатор регистрации пользователя"""
    email = serializers.EmailField()

    class Meta(UserCreateSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def validate_email(self, value):
        lower_email = value.lower()
        if User.objects.filter(email__iexact=lower_email).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже зарегистрирован'
            )

        return lower_email

    def validate_username(self, value):
        lower_username = value.lower()
        if User.objects.filter(username__iexact=lower_username).exists():
            raise serializers.ValidationError(
                'Пользователь с таким username уже зарегистрирован'
            )

        return lower_username


class CustomTokenCreateSerializer(TokenCreateSerializer):
    """Сериализатор получения токена"""
    def validate_email(self, value):
        return value.lower()


class CustomUserSerializer(UserSerializer):
    """Сериализатор получения пользователя"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        lookup_field = ('username',)

    def get_is_subscribed(self, instance):
        if self.context:
            return (
                self.context.get('request').user.is_authenticated
                and Follow.objects.filter(
                    user=self.context['request'].user,
                    author=instance
                ).exists()
            )
        return False


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор получения ингредиентов рецепта"""
    id = serializers.IntegerField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit')

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )
        model = IngredientRecipe


class CreateRecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор создания ингредиентов рецепта"""
    amount = serializers.IntegerField()
    id = serializers.IntegerField(source='ingredients.id')

    class Meta:
        model = Ingredients
        fields = ('id', 'amount')

    def validate_id(self, id):
        if not Ingredients.objects.filter(id=id).exists():
            raise NotFound(detail='Ингредиент не найден.')
        return id

    def validate_amount(self, amount):
        if amount <= 0:
            raise serializers.ValidationError(
                'Убедитесь, что это значение больше либо равно 1'
            )
        return amount


class TagsSerializer(serializers.ModelSerializer):
    """Сериализатор получения тегов"""
    class Meta:
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )
        model = Tags


class RecipesSerializer(RecipeFieldsMixin, serializers.ModelSerializer):
    """Сериализатор получения рецептов"""
    tags = TagsSerializer(many=True)
    ingredients = IngredientRecipeSerializer(many=True)
    author = CustomUserSerializer()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe


class CreateRecipesSerializer(RecipeFieldsMixin, serializers.ModelSerializer):
    """Сериализатор создания/обновления рецептов"""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(),
        many=True
    )
    ingredients = CreateRecipeIngredientSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe

    def validate_ingredients(self, value_list):
        if value_list == []:
            raise serializers.ValidationError(
                'Нужно указать минимум 1 ингредиент.'
            )
        for value in value_list:
            if 'ingredients' not in value:
                raise serializers.ValidationError(
                    'ingredients - Обязательное поле.'
                )
        inrgedients = [
            item['ingredients']['id'] for item in value_list
        ]
        unique_ingredients = set(inrgedients)
        if len(inrgedients) != len(unique_ingredients):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальны.'
            )
        return value_list

    def validate_tags(self, value_list):
        if value_list == []:
            raise serializers.ValidationError(
                'Нужно указать минимум 1 тег.'
            )

        return value_list

    def validate(self, value_list):
        for field in ['name', 'text', 'cooking_time']:
            if not value_list.get(field):
                raise serializers.ValidationError(
                    f'{field} - Обязательное поле.'
                )
        return value_list

    @transaction.atomic
    def ingredients_tags_set(self, recipe, tags, ingredients):
        IngredientRecipe.objects.bulk_create(
            [IngredientRecipe(
                recipe=recipe,
                ingredients=Ingredients.objects.get(
                    pk=ingredient['ingredients']['id']
                ),
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )
        recipe.tags.set(tags)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        image_data = validated_data.pop('image')
        recipe = Recipe.objects.create(**validated_data)
        recipe.image.save('recipe_image.png', image_data, save=True)
        self.ingredients_tags_set(recipe, tags, ingredients)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        IngredientRecipe.objects.filter(
            recipe=instance,
            ingredients__in=instance.ingredient.all()).delete()
        self.ingredients_tags_set(instance, tags, ingredients)
        instance.save()

        return instance


class RecipesNoAuthorSerializer(serializers.ModelSerializer):
    """Сериализатор получения автора сокращенный"""

    def validate(self, validated_data):
        user = self.initial_data['user']
        recipe = self.initial_data['recipe']
        if ShoppingCart.objects.filter(
            user=user,
            recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                {'errors': 'Рецепт уже в корзине'}
            )
        if not Recipe.objects.filter(id=recipe.id).exists():
            raise serializers.ValidationError(
                {'errors': 'Рецепт не найден'}
            )

        return validated_data

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        model = Recipe


class SubscriptionsSerializer(CustomUserSerializer):
    """Сериализатор получения подписок"""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes_count(self, instance):
        return instance.recipes.count()

    def get_recipes(self, instance):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = instance.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipesNoAuthorSerializer(
            recipes,
            many=True,
            read_only=True
        )
        return serializer.data


class SubscribeSerializer(CustomUserSerializer):
    """Сериализатор создания подписки"""
    recipes = RecipesNoAuthorSerializer(
        many=True,
        read_only=True,
        instance='follower'
    )
    recipes_count = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        model = User

    def get_recipes_count(self, instance):
        return instance.recipes.count()

    def validate(self, validated_data):
        user = self.initial_data['user']
        author = self.initial_data['author']
        if user == author:
            raise serializers.ValidationError(
                {'errors': 'Нельзя подписаться на себя'}
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                {'errors': 'Вы уже подписаны на этого автора'}
            )

        return validated_data


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор получения ингредиентов"""
    class Meta:
        fields = '__all__'
        model = Ingredients


class FavoriteRecipesViewSetSerializer(serializers.ModelSerializer):
    """Сериализатор получения избранных рецептов"""
    class Meta:
        fields = '__all__'
        model = FavoriteRecipe

    def create(self, validated_data):
        user_data = validated_data.get('user')
        recipe_data = validated_data.get('recipe')

        favorite_recipe, created = FavoriteRecipe.objects.get_or_create(
            **validated_data
        )
        if not created:
            favorite_recipe.recipe_id = recipe_data.pk
            favorite_recipe.user = user_data
            favorite_recipe.save()
        return favorite_recipe


class DownloadShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор скачивания продуктов"""
    class Meta:
        fields = '__all__'
        model = User
