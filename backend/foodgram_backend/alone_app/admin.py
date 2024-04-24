from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Tag, Ingredient, Recipe, FoodgramUser


class TagInline(admin.StackedInline):
    model = Tag.recipes.through
    extra = 1


class IngredientInline(admin.StackedInline):
    model = Ingredient.recipes.through
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
    )
    search_fields = ('name',)


@admin.register(FoodgramUser)
class FoodgramUser(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_superuser'
    )
    search_fields = ('username', 'email',)
    list_filter = ('first_name', 'email',)


@admin.register(Recipe)
class Recipe(admin.ModelAdmin):
    inlines = (
        TagInline,
        IngredientInline,
    )
    list_display = (
        'name',
        'author',
    )
    list_filter = ('author', 'tags',)


@admin.register(Ingredient)
class Ingredient(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name',)
    list_filter = ('name', 'measurement_unit')


admin.site.unregister(Group)
