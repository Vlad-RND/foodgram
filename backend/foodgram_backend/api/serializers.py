from drf_extra_fields.fields import Base64ImageField

from django.core.files.base import ContentFile
from rest_framework import serializers, pagination

from recipes.models import (Tag, Ingredient, Recipe, FoodgramUser,
                            IngredientRecipe, Subscription,
                            Favorites, ShoppingList)
from recipes.constants import MIN_VALUE, MAX_VALUE


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор для получения кастомной модели пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(default=0)

    class Meta:
        model = FoodgramUser
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'is_subscribed', 'recipes_count')

    def get_is_subscribed(self, obj):
        if 'request' in self.context:
            current_user = self.context['request'].user
            if current_user == obj:
                return False
            elif Subscription.objects.filter(
                follower=current_user.id,
                author=obj.id
            ).exists():
                return True
            return False


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
        req = self.context['request'] if 'request' in self.context else False

        return all(
            [
                req,
                req.user.is_authenticated,
                obj.favorites.filter(user=req.user.id).exists()
            ]
        )

    def get_is_in_shopping_cart(self, obj):
        req = self.context['request'] if 'request' in self.context else False

        return all(
            [
                req,
                req.user.is_authenticated,
                obj.shopping_list.filter(user=req.user.id).exists()
            ]
        )


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор добавления ингредиента в рецепт. """

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
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
        if 'ingredients' not in data or 'tags' not in data:
            raise serializers.ValidationError(
                'Отсутствует список ингредиентов или тегов.'
            )

        ingredient_list = [
            ingredient['ingredient'] for ingredient in data['ingredients']
        ]
        if not len(ingredient_list) == len(set(ingredient_list)):
            raise serializers.ValidationError('Этот ингредиент уже добавлен.')

        tag_list = data['tags']
        if not len(tag_list) == len(set(tag_list)):
            raise serializers.ValidationError('Тег уже есть в рецепте.')
        return super().validate(data)

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
                ingredient_id=ingredient['ingredient'].id,
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
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = ('recipes', 'first_name', 'last_name', 'is_subscribed',)

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj)
        request = self.context['request']
        limit = request.query_params['recipes_limit']
        if limit:
            recipes = recipes[:int(limit)]
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context={'request': request}
        ).data


class CreateSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор создания модели Subscription."""

    follower = serializers.PrimaryKeyRelatedField(
        queryset=FoodgramUser.objects.all()
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=FoodgramUser.objects.all()
    )

    class Meta:
        model = Subscription
        fields = ('follower', 'author')

    def to_representation(self, instance):
        current_user = instance.follower

        serializer = FoodgramUserSerializer(
            instance=FoodgramUser.objects.get(
                pk=instance.author.id
            )
        )
        data = serializer.data
        data['is_subscribed'] = Subscription.objects.filter(
            follower=current_user.id,
            author=instance.author
        ).exists()

        paginator = pagination.PageNumberPagination()
        paginator.page_size = 3
        current_recipes = Recipe.objects.filter(
            author=instance.author
        )
        page = paginator.paginate_queryset(
            current_recipes,
            self.context['request']
        )
        serializer = ShortRecipeSerializer(
            page, many=True, context=self.context
        )

        data['recipes'] = serializer.data
        data['recipes_count'] = len(current_recipes)

        return data

    def validate(self, data):
        current_user = data['follower']
        author = data['author']

        if current_user == author:
            raise serializers.ValidationError(
                {"detail": "Нельзя подписываться на самого себя"}
            )
        if Subscription.objects.filter(
            follower=current_user.id,
            author=author.id
        ).exists():
            raise serializers.ValidationError({"detail": "Уже подписан"})

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

        if not Recipe.objects.filter(pk=recipe_id):
            raise serializers.ValidationError(
                {self.Meta.model._meta.verbose_name: "Рецепт не найден."}
            )

        if self.Meta.model.objects.filter(
            user=current_user_id,
            recipe=recipe_id
        ).exists():
            raise serializers.ValidationError(
                {self.Meta.model._meta.verbose_name: "Уже в избранном"}
            )

        return data


class FavoritesSerializer(FavoritesShoppingListSerializer):
    """Сериализатор модели Favorites."""

    user = serializers.PrimaryKeyRelatedField(
        queryset=FoodgramUser.objects.all()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta(FavoritesShoppingListSerializer.Meta):
        model = Favorites


class ShoppingListSerializer(FavoritesShoppingListSerializer):
    """Сериализатор модели ShoppingList."""

    user = serializers.PrimaryKeyRelatedField(
        queryset=FoodgramUser.objects.all()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta(FavoritesShoppingListSerializer.Meta):
        model = ShoppingList
