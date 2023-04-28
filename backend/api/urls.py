from django.urls import include, path  # , re_path
from rest_framework.routers import DefaultRouter

from .views import (ActivateUser, CustomUserViewSet,
                    DownloadShoppingCartViewSet, FavoriteRecipesViewSet,
                    IngredientsViewSet, RecipesViewSet, ShoppingCartViewSet,
                    SubscriptionsViewSet, TagsViewSet)

v1_router = DefaultRouter()
v1_router.register('tags', TagsViewSet, basename='tags')
v1_router.register(r'ingredients', IngredientsViewSet, basename='ingredients')
v1_router.register(
    'recipes/download_shopping_cart',
    DownloadShoppingCartViewSet,
    basename='download_shopping_cart',
)
v1_router.register('recipes', RecipesViewSet, basename='recipes')
v1_router.register(
    r'^recipes/(?P<recipes_id>\d+)/shopping_cart',
    ShoppingCartViewSet,
    basename='shopping_cart',
)
v1_router.register(
    r'^recipes/(?P<recipes_id>\d+)/favorite',
    FavoriteRecipesViewSet,
    basename='favorites',
)
v1_router.register(
    r'^users/(?P<user_id>\d+)/subscribe',
    SubscriptionsViewSet,
    basename='subscribe',
)
v1_router.register(
    'users/subscriptions', SubscriptionsViewSet, basename='subscriptions'
)
v1_router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(v1_router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'account/activate/<uid>/<token>',
        ActivateUser.as_view({'get': 'activation'}),
        name='activation',
    ),
]
