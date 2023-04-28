from django.db.models import Case, Q, When
from django.db.models.functions import Lower
from django_filters.rest_framework import FilterSet, filters

from recipes.models import Recipe, Tags


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             to_field_name='slug',
                                             queryset=Tags.objects.all())

    author = filters.CharFilter(
        method='filter_author'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='is_in_shopping_cart_filter'
    )
    is_favorited = filters.BooleanFilter(
        method='is_favorited_filter'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author',)

    def filter_author(self, queryset, name, value):
        filter_author = self.request.query_params.get('author')
        if filter_author:
            return queryset.filter(author=filter_author)
        return queryset

    def is_in_shopping_cart_filter(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(recipe_in_cart__user=user)
        return queryset

    def is_favorited_filter(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite_recipe__user=user)
        return queryset


class IngredientsFilter(FilterSet):

    def filter_queryset(self, queryset):
        search_query = self.request.query_params.get('name')
        if search_query:
            queryset = queryset.filter(
                Q(
                    name__startswith=search_query
                ) | Q(
                    name__icontains=search_query
                )
            ).annotate(
                lower_name=Lower('name')
            ).order_by(
                Case(
                    When(
                        lower_name__startswith=search_query, then=0
                    ), default=1
                ), 'name'
            )

        return queryset
