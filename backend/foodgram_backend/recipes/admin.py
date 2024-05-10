from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .models import (Tag, Ingredient, Recipe,
                     FoodgramUser, Favorites, Subscription,
                     ShoppingList)


class IngredientInline(admin.StackedInline):
    model = Ingredient.recipes.through
    extra = 1
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'id',
    )
    search_fields = ('name',)


@admin.register(FoodgramUser)
class FoodgramUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_superuser',
        'id',
        'get_recipies',
        'get_followers',
    )
    search_fields = ('username', 'email',)
    list_filter = ('first_name', 'email',)

    @admin.display(description='Кол-во рецептов', )
    def get_recipies(self, obj):
        return obj.recipes.count()

    @admin.display(description='Кол-во подписчиков', )
    def get_followers(self, obj):
        return obj.author.count()


@admin.register(Recipe)
class Recipe(admin.ModelAdmin):
    inlines = (
        IngredientInline,
    )
    list_display = (
        'name',
        'author',
        'get_favorites',
        'get_ingredient',
    )
    list_filter = ('author', 'tags',)

    @admin.display(
        description='В избранном',
    )
    def get_favorites(self, obj):
        """Получения количества добавлений в избранное."""
        return obj.favorites.count()

    @admin.display(
        description='Ингредиенты',
    )
    def get_ingredient(self, obj):
        result = ''
        for i in obj.ingredient_recipe.all():
            result += (f'{i.ingredient.name} {i.amount} '
                       f'{i.ingredient.measurement_unit}, ')
        return result[:-2]

    def image(self, obj):
        return mark_safe(
            f'<img src={obj.image.url} width="80" height="60">'
        )


@admin.register(Ingredient)
class Ingredient(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
        'id',
    )
    search_fields = ('name',)
    list_filter = ('name', 'measurement_unit')


@admin.register(Subscription)
class Subscription(admin.ModelAdmin):
    list_display = (
        'follower',
        'author',
    )
    search_fields = ('follower',)
    list_filter = ('follower',)


@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = ('user',)
    list_filter = ('user', 'recipe')


@admin.register(ShoppingList)
class ShoppingList(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = ('user',)
    list_filter = ('user', 'recipe')


admin.site.unregister(Group)
