from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Tag, Ingredient, Recipe, FoodgramUser,
                            IngredientRecipe, Subscription,
                            Favorites, ShoppingList)
from recipes.constants import MIN_VALUE, MAX_VALUE


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор для получения кастомной модели пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'is_subscribed',)

    def get_is_subscribed(self, obj):
        req = self.context['request']

        return req and req.user.is_authenticated and obj.author.filter(
            follower=req.user.id
        ).exists()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели Тега."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели Ингредиента."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор связующей модели Ингредиент-Рецепт."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class CommonRecipeSerializer(serializers.ModelSerializer):
    """Общий сериализатор для модели Recipe"""

    author = FoodgramUserSerializer(read_only=True)
    image = Base64ImageField(allow_null=False, allow_empty_file=False)


class ShowRecipeSerializer(CommonRecipeSerializer):
    """Сериализатор модели Recipe с показом полной информации о модели."""

    tags = TagSerializer(many=True)
    ingredients = IngredientRecipeSerializer(
        source='ingredient_recipe', many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'image', 'text',
            'cooking_time', 'is_favorited', 'is_in_shopping_cart',
        )
        read_only_fields = ('author',)

    def get_is_favorited(self, obj):
        req = self.context['request']

        return req and req.user.is_authenticated and obj.favorites.filter(
            user=req.user.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        req = self.context['request']

        return req and req.user.is_authenticated and obj.shopping_list.filter(
            user=req.user.id
        ).exists()


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор добавления ингредиента в рецепт. """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=MIN_VALUE, max_value=MAX_VALUE
    )

    class Meta:
        model = IngredientRecipe
        fields = (
            'id',
            'amount',
        )


class CreateRecipeSerializer(CommonRecipeSerializer):
    """Сериализатор создания модели Recipe."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = AddIngredientRecipeSerializer(many=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_VALUE, max_value=MAX_VALUE
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
        )
        read_only_fields = ('author',)

    def validate(self, data):
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                {'ingredients': 'Отсутствует список ингредиентов.'}
            )
        if 'tags' not in data:
            raise serializers.ValidationError(
                {'tags': 'Отсутствует список тегов.'}
            )

        ingredient_list = [
            ingredient['id'] for ingredient in data['ingredients']
        ]
        if not len(ingredient_list) == len(set(ingredient_list)):
            raise serializers.ValidationError(
                {'ingredients': 'Этот ингредиент уже добавлен.'}
            )

        tag_list = data['tags']
        if not len(tag_list) == len(set(tag_list)):
            raise serializers.ValidationError(
                {'tags': 'Тег уже есть в рецепте.'}
            )
        return data

    def to_representation(self, instance):
        return ShowRecipeSerializer(instance, context=self.context).data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        self.create_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    @staticmethod
    def create_ingredients(ingredients, recipe):
        recipe_ingredients = [
            IngredientRecipe(
                ingredient_id=ingredient['id'].id,
                recipe=recipe,
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        IngredientRecipe.objects.bulk_create(recipe_ingredients)

    def update(self, instance, validated_data):
        instance.tags.clear()
        IngredientRecipe.objects.filter(recipe=instance).delete()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        self.create_ingredients(ingredients, instance)

        return super().update(instance, validated_data)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор получения короткого описания модели Recipe."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class GetSubscriptionSerializer(FoodgramUserSerializer):
    """Сериализатор модели Subscription."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(default=0)

    class Meta(FoodgramUserSerializer.Meta):
        model = FoodgramUser
        fields = FoodgramUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        request = self.context['request']
        limit = request.query_params.get('recipes_limit')
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                pass
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context=self.context
        ).data


class CreateSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор создания модели Subscription."""

    class Meta:
        model = Subscription
        fields = ('follower', 'author')

    def to_representation(self, instance):
        return GetSubscriptionSerializer(
            instance=instance.follower,
            context=self.context
        ).data

    def validate(self, data):
        current_user = data['follower']
        author = data['author']

        if current_user == author:
            raise serializers.ValidationError(
                {'detail': 'Нельзя подписываться на самого себя'}
            )
        if author.author.filter(follower=current_user).exists():
            raise serializers.ValidationError({'detail': 'Уже подписан'})

        return data


class FavoritesShoppingListSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для Favorites и ShoppingList."""
    class Meta:
        fields = ('user', 'recipe',)

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance=instance.recipe
        ).data

    def validate(self, data):
        current_user_id = data['user'].id
        recipe_id = data['recipe'].id
        model = self.Meta.model

        if model.objects.filter(
            user=current_user_id,
            recipe=recipe_id
        ).exists():
            raise serializers.ValidationError(
                {model._meta.verbose_name: f'Уже в {model._meta.verbose_name}'}
            )

        return data


class FavoritesSerializer(FavoritesShoppingListSerializer):
    """Сериализатор модели Favorites."""

    class Meta(FavoritesShoppingListSerializer.Meta):
        model = Favorites


class ShoppingListSerializer(FavoritesShoppingListSerializer):
    """Сериализатор модели ShoppingList."""

    class Meta(FavoritesShoppingListSerializer.Meta):
        model = ShoppingList
