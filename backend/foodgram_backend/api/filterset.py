import django_filters
from django_filters import rest_framework as filters

from recipes.models import Recipe, Ingredient


class RecipeFilter(filters.FilterSet):
    """Описывает логику фильтрации модели Recipe."""

    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        label='Tags'
    )
    is_favorited = filters.BooleanFilter(
        method='get_favorite',
        label='Favourited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_shopping_cart',
        label='Shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_favorite(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method='name_filter')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def name_filter(self, queryset, name, value):
        return queryset.filter(name__icontains=value)
