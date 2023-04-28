from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import AllowAny
from rest_framework import serializers

from recipes.models import FavoriteRecipe,  ShoppingCart


class ReadOnlyUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (filters.SearchFilter, )
    search_fields = ('^name', )


class RecipeFieldsMixin(serializers.Serializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_in_shopping_cart(self, instance):

        if (
            self.context.get('request')
            and not self.context['request'].user.is_anonymous
        ):
            return ShoppingCart.objects.filter(
                recipe=instance.recipe_in_cart.instance,
                user=self.context['request'].user,
            ).exists()
        return False

    def get_is_favorited(self, instance):

        if (
            self.context.get('request')
            and not self.context['request'].user.is_anonymous
        ):
            return FavoriteRecipe.objects.filter(
                recipe=instance.favorite_recipe.instance,
                user=self.context['request'].user,
            ).exists()

        return False
