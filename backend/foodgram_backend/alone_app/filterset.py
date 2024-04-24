from django_filters import rest_framework as filters

from .models import Recipe


class RecipeFilter(filters.FilterSet):
    """Описывает логику фильтрации модели Recipe."""

    author = filters.Filter()
    tags = filters.AllValuesMultipleFilter(
        field_name='tag_recipe__tag__slug',
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
            return Recipe.objects.filter(recipe__user=self.request.user)
        return Recipe.objects.all()

    def get_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return Recipe.objects.filter(
                buy_recipe__customer=self.request.user
            )
        return Recipe.objects.all()
