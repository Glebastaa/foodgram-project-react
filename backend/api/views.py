from backend.settings import BASE_DIR
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientsFilter, RecipeFilter
from .mixins import ReadOnlyUserViewSet
from .pagination import CustomPaginator
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    CreateRecipesSerializer,
    FavoriteRecipesViewSetSerializer,
    IngredientsSerializer,
    RecipesNoAuthorSerializer,
    RecipesSerializer,
    TagsSerializer,
    CustomUserSerializer,
    DownloadShoppingCartSerializer,
    SubscribeSerializer,
    SubscriptionsSerializer,
)
from recipes.models import (
    FavoriteRecipe,
    IngredientRecipe,
    Ingredients,
    Recipe,
    ShoppingCart,
    Tags,
    User,
)
from users.models import Follow


class ActivateUser(UserViewSet):
    """Активация аккаунта по ссылке из email"""
    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        kwargs['data'] = {
            'uid': self.kwargs['uid'],
            'token': self.kwargs['token']
        }

        return serializer_class(*args, **kwargs)


class CustomUserViewSet(UserViewSet):
    """Вьюсет модели пользователя"""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (AllowAny,)

    @action(
        methods=['get', ],
        detail=False,
        url_path='me',
        permission_classes=(IsAuthenticated,),
    )
    def get_me(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagsViewSet(ReadOnlyUserViewSet):
    """Вьюсет модели тегов"""
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer


class IngredientsViewSet(ReadOnlyUserViewSet):
    """Вьюсет модели ингредиентов"""
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientsFilter


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет модели рецептов"""
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = CustomPaginator
    queryset = Recipe.objects.all()
    ordering_fields = ('-pub_date',)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:

            return CreateRecipesSerializer

        return RecipesSerializer

    def create(self, request):
        data = request.data.copy()
        data['author'] = request.user.id
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except NotFound as e:
            return Response({'detail': str(e)}, status=e.status_code)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class FavoriteRecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет модели избранных рецептов"""
    serializer_class = FavoriteRecipesViewSetSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        data['recipe'] = kwargs['recipes_id']
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def delete(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        data['recipe'] = kwargs['recipes_id']
        serializer = self.get_serializer(data=data)
        if serializer.is_valid(raise_exception=True):
            get_object_or_404(
                FavoriteRecipe, recipe_id=data['recipe'], user=data['user']
            ).delete()

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_204_NO_CONTENT, headers=headers
        )


class SubscriptionsViewSet(viewsets.ModelViewSet):
    """Вьюсет модели подписки на авторов"""
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPaginator

    def get_serializer_class(self):
        if self.action in ['create', 'delete']:

            return SubscribeSerializer

        return SubscriptionsSerializer

    def get_queryset(self):
        return User.objects.filter(
            follower__user__pk=self.request.user.pk,
        )

    def create(self, request, *args, **kwargs):
        author = get_object_or_404(User, pk=kwargs['user_id'])
        data = request.data.copy()
        data['user'] = request.user
        data['author'] = author
        serializer = self.get_serializer(
            author,
            data=data
        )
        serializer.is_valid(raise_exception=True)
        Follow.objects.create(
            user=request.user,
            author=author
        )
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, *args, **kwargs):
        author = get_object_or_404(User, pk=kwargs['user_id'])
        get_object_or_404(
            Follow,
            user=request.user,
            author=author
        ).delete()
        return Response({'detail': 'Вы отписаны'},
                        status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """Вьюсет модели корзины"""
    serializer_class = RecipesNoAuthorSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs['recipes_id'])
        data = request.data.copy()
        data['recipe'] = recipe
        data['user'] = request.user
        data['name'] = recipe.name
        data['image'] = recipe.image
        serializer = self.get_serializer(
            recipe,
            data=data
        )
        serializer.is_valid(raise_exception=True)
        ShoppingCart.objects.create(
            user=request.user,
            recipe=recipe
        )
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs['recipes_id'])
        get_object_or_404(
            ShoppingCart,
            user=request.user,
            recipe=recipe
        ).delete()
        return Response({'detail': 'Удалено из корзины'},
                        status=status.HTTP_204_NO_CONTENT)


class DownloadShoppingCartViewSet(viewsets.ModelViewSet):
    """Вьюсет скачивания списка продуктов"""
    permission_classes = (IsAuthenticated,)
    serializer_class = DownloadShoppingCartSerializer
    pdfmetrics.registerFont(TTFont('arial', BASE_DIR + '/fonts/arial.ttf'))

    def list(self, request):

        filtered_ingredients = (
            IngredientRecipe.objects
            .filter(recipe__recipe_in_cart__user=request.user)
            .values('ingredients')
            .annotate(total_amount=Sum('amount'))
            .values_list('ingredients__name', 'total_amount',
                         'ingredients__measurement_unit')
        )

        ingredients_dict = {}
        for ingredient, amount, unit in filtered_ingredients:
            if ingredient in ingredients_dict:
                ingredients_dict[ingredient]['amount'] += amount
            else:
                ingredients_dict[ingredient] = {
                    'amount': amount,
                    'unit': unit or ''
                }

        ingredients_list = [
            {
                'name': ingredient,
                'amount': data['amount'],
                'unit': data['unit']
            }
            for ingredient, data in ingredients_dict.items()
        ]

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="cart.pdf"'
        response['Content-Encoding'] = 'utf-8'
        p = canvas.Canvas(response)
        p.setFont('arial', 22)
        p.drawString(100, 750, 'Список покупок:')

        y = 700
        for ingredient in ingredients_list:
            y -= 30
            p.drawString(
                100,
                y, (
                    f"- {ingredient['name']}"
                    f" - {ingredient['amount']}"
                    f" {ingredient['unit']}"
                ),
            )

        p.showPage()
        p.save()

        return response
