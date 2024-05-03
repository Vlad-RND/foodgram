import base64
import webcolors

from django.core.files.base import ContentFile
from rest_framework import exceptions, serializers, pagination

from .models import (Tag, Ingredient, Recipe, FoodgramUser,
                     IngredientRecipe, Subscription, TagRecipe,
                     Favorites, ShoppingList)


class Hex2NameColor(serializers.Field):
    """Кодирование цвета в код HEX."""

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class Base64ImageField(serializers.ImageField):
    """Кодирование изображения Base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор для получения кастомной модели пользователя."""

    class Meta:
        model = FoodgramUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if 'request' in self.context:
            current_user = self.context['request'].user
            if current_user == instance:
                data['is_subscribed'] = False
            elif Subscription.objects.filter(
                base_user=current_user.id,
                follow_user=instance.id
            ).exists():
                data['is_subscribed'] = True
        return data


class FoodgramUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и изменения кастомной модели пользователя."""

    class Meta:
        model = FoodgramUser
        fields = ('id', 'username', 'email',
                  'first_name', 'last_name', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = FoodgramUser(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели Тега."""

    color = Hex2NameColor()

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
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CommonRecipeSerializer(serializers.ModelSerializer):
    """Общий сериализатор для модели Recipe"""

    author = FoodgramUserSerializer(read_only=True)
    image = Base64ImageField()


class ShowRecipeSerializer(CommonRecipeSerializer):
    """Сериализатор модели Recipe с показом полной информации о модели."""

    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'image', 'text',
            'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = ('author',)

    def get_ingredients(self, obj):
        queryset = IngredientRecipe.objects.filter(
            recipe=obj).select_related(
            'recipe', 'ingredient')
        return IngredientRecipeSerializer(queryset, many=True).data

    def get_is_favorited(self, obj):
        return Favorites.objects.filter(
            user=self.context['request'].user.id,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingList.objects.filter(
            customer=self.context['request'].user.id,
            recipe=obj
        ).exists()


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор добавления ингредиента в рецепт. """

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = [
            'id',
            'amount'
        ]


class CreateRecipeSerializer(CommonRecipeSerializer):
    """Сериализатор создания модели Recipe."""

    tags = serializers.ListField(write_only=True, min_length=1)
    ingredients = AddIngredientRecipeSerializer(many=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('author',)

    def validate(self, data):
        if 'ingredients' not in data or 'tags' not in data:
            raise serializers.ValidationError(
                'Отсутствует список ингредиентов или.'
            )

        ingredient_list = []
        for ingredient in data['ingredients']:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise serializers.ValidationError(
                    'Такого ингридиента не существует'
                )
            if int(ingredient['amount']) < 1:
                raise serializers.ValidationError(
                    {'amount': 'Убедитесь, что значение больше либо равно 1.'}
                )
            if ingredient['id'] in ingredient_list:
                raise serializers.ValidationError(
                    'Этот ингредиент уже добавлен.'
                )
            else:
                ingredient_list.append(ingredient['id'])

        tag_list = []
        for tag in data['tags']:
            if not Tag.objects.filter(id=tag).exists():
                raise serializers.ValidationError(
                    'Такого тега не существует'
                )
            if tag in tag_list:
                raise serializers.ValidationError(
                    'Тег уже есть в рецепте.'
                )
            else:
                tag_list.append(tag)
        return super().validate(data)

    def to_representation(self, instance):
        return ShowRecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def create_ingredients(self, ingredients, recipe):
        recipe_ingredients = [
            IngredientRecipe(
                ingredient_id=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        IngredientRecipe.objects.bulk_create(recipe_ingredients)

    def update(self, instance, validated_data):
        TagRecipe.objects.filter(recipe=instance).delete()
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


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор модели Subscription."""

    base_user = serializers.SlugRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault(),
        slug_field='username'
    )

    class Meta:
        model = Subscription
        fields = ('id', 'base_user',)

    def to_representation(self, instance):
        current_user = instance.base_user

        if self.context['request'].method == 'GET':
            subscription_list = Subscription.objects.filter(
                base_user=current_user
            )
        else:
            subscription_list = [instance]

        for subscription in subscription_list:
            serializer = FoodgramUserSerializer(
                instance=FoodgramUser.objects.get(
                    pk=subscription.follow_user.id
                )
            )
            data = serializer.data
            data['is_subscribed'] = Subscription.objects.filter(
                base_user=current_user.id,
                follow_user=subscription.follow_user
            ).exists()

        paginator = pagination.PageNumberPagination()
        paginator.page_size = 3
        current_recipes = Recipe.objects.filter(
            author=subscription.follow_user
        )
        page = paginator.paginate_queryset(
            current_recipes,
            self.context['request']
        )
        serializer = ShortRecipeSerializer(page, many=True, context={
            'request': self.context['request']})

        data['recipes'] = serializer.data
        data['recipes_count'] = len(current_recipes)

        return data

    def validate(self, data):
        current_user = self.context['request'].user
        follow_user_id = self.context['view'].kwargs['user_id']

        if not FoodgramUser.objects.filter(pk=follow_user_id):
            raise exceptions.NotFound()
        follow_user = FoodgramUser.objects.get(pk=follow_user_id)

        if current_user == follow_user:
            raise serializers.ValidationError(
                {"detail": "Нельзя подписываться на самого себя"}
            )
        if Subscription.objects.filter(
            base_user=current_user.id,
            follow_user=follow_user_id
        ).exists():
            raise serializers.ValidationError({"detail": "Уже подписан"})

        return super().validate(data)

    def create(self, validated_data):
        return Subscription.objects.create(
            base_user=validated_data['base_user'],
            follow_user=FoodgramUser.objects.get(
                pk=self.context['view'].kwargs['user_id']
            ),
        )


class FavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор модели Favorites."""

    user = serializers.SlugRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault(),
        slug_field='username'
    )

    class Meta:
        model = Favorites
        fields = ('id', 'user',)

    def to_representation(self, instance):
        recipe = Recipe.objects.get(pk=instance.recipe.id)
        base_url = self.context['request'].build_absolute_uri().split('api')[0]
        data = {
            "id": recipe.id,
            "name": recipe.name,
            "image": base_url + str(recipe.image),
            "cooking_time": recipe.cooking_time
        }
        return data

    def validate(self, data):
        current_user = self.context['request'].user
        recipe_id = self.context['view'].kwargs['recipe_id']

        if not Recipe.objects.filter(pk=recipe_id):
            raise serializers.ValidationError(
                {"detail": "Рецепт не найден."}
            )

        if Favorites.objects.filter(
            user=current_user.id,
            recipe=recipe_id
        ).exists():
            raise serializers.ValidationError(
                {"detail": "Уже в избранном"}
            )

        return super().validate(data)

    def create(self, validated_data):
        return Favorites.objects.create(
            user=validated_data['user'],
            recipe=Recipe.objects.get(
                pk=self.context['view'].kwargs['recipe_id']
            ),
        )


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор модели ShoppingList."""

    customer = serializers.SlugRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault(),
        slug_field='username'
    )

    class Meta:
        model = ShoppingList
        fields = ('id', 'customer',)

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance=Recipe.objects.get(pk=instance.recipe.id)
        ).data

    def validate(self, data):
        current_user = self.context['request'].user
        recipe_id = self.context['view'].kwargs['recipe_id']

        if not Recipe.objects.filter(pk=recipe_id):
            raise serializers.ValidationError(
                {"detail": "Рецепт не найден."}
            )

        if ShoppingList.objects.filter(
            customer=current_user.id,
            recipe=recipe_id
        ).exists():
            raise serializers.ValidationError(
                {"detail": "Уже в списке покупок."}
            )

        return super().validate(data)

    def create(self, validated_data):
        return ShoppingList.objects.create(
            customer=validated_data['user'],
            recipe=Recipe.objects.get(
                pk=self.context['view'].kwargs['recipe_id']
            ),
        )
