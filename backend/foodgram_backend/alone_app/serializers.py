import base64
import webcolors

from django.core.files.base import ContentFile
from rest_framework import exceptions, serializers

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
            if self.context['request'].user == instance:
                data['is_subscribed'] = False
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

    name = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_amount(self, obj):
        return obj.amount

    def get_name(self, obj):
        return Ingredient.objects.get(name=obj.ingredient).name

    def get_measurement_unit(self, obj):
        return Ingredient.objects.get(name=obj.ingredient).measurement_unit


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
        return IngredientRecipeSerializer(
            IngredientRecipe.objects.filter(recipe=obj.id),
            many=True
        ).data

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


class CreateRecipeSerializer(CommonRecipeSerializer):
    """Сериализатор создания модели Recipe."""

    tags = serializers.ListField(write_only=True)
    ingredients = serializers.ListField(write_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('author',)

    def validate(self, data):
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                {'ingredients': 'Отсутствует список ингредиентов.'}
            )
        elif not data['ingredients']:
            raise serializers.ValidationError(
                {'ingredients': 'Отсутствует список ингредиентов.'}
            )
        ingredient_list = []
        for ingredient in data['ingredients']:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise serializers.ValidationError(
                    {'ingredients': 'Такого ингридиента не существует'}
                )
            if not ingredient['amount'].isdigit():
                raise serializers.ValidationError(
                    {'amount': 'Убедитесь, что значение - число.'}
                )
            if int(ingredient['amount']) < 1:
                raise serializers.ValidationError(
                    {'amount': 'Убедитесь, что значение больше либо равно 1.'}
                )
            if ingredient['id'] in ingredient_list:
                raise serializers.ValidationError(
                    {'ingredients': 'Ингридиент уже есть в рецепте.'}
                )
            else:
                ingredient_list.append(ingredient['id'])

        if 'tags' not in data:
            raise serializers.ValidationError(
                {'tags': 'Отсутствует список тегов.'}
            )
        elif not data['tags']:
            raise serializers.ValidationError(
                {'tags': 'Отсутствует список тегов.'}
            )

        tag_list = []
        for tag in data['tags']:
            if not Tag.objects.filter(id=tag).exists():
                raise serializers.ValidationError(
                    {'tags': 'Такого тега не существует'}
                )
            if tag in tag_list:
                raise serializers.ValidationError(
                    {'tags': 'Тег уже есть в рецепте.'}
                )
            else:
                tag_list.append(tag)

            if data['cooking_time'] < 1:
                raise serializers.ValidationError(
                    {'cooking_time': 'Не может быть меньше 1.'}
                )

        return super().validate(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        current_tag_recipes = TagRecipe.objects.filter(recipe=instance.id)
        current_ingredient_recipie = IngredientRecipe.objects.filter(
            recipe=instance.id
        )

        tags_list = []
        for i in current_tag_recipes:
            tags_list.append(
                TagSerializer(
                    instance=Tag.objects.get(name=i.tag)
                ).data
            )

        ingredients_list = []
        for i in current_ingredient_recipie:
            ingredient = Ingredient.objects.get(name=i.ingredient)
            ingredients_list.append(
                {
                    'id': ingredient.id,
                    'name': ingredient.name,
                    'measurement_unit': ingredient.measurement_unit,
                    'amount': i.amount
                }
            )

        data['ingredients'] = ingredients_list
        data['tags'] = tags_list
        data['is_favorited'] = False
        data['is_in_shopping_cart'] = False
        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)

        for tag in tags:
            TagRecipe.objects.create(
                tag=Tag.objects.get(pk=tag),
                recipe=recipe
            )

        for ingredient in ingredients:
            IngredientRecipe.objects.create(
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        for ingredient in ingredients:
            ingredient_recipe, status = IngredientRecipe.objects.get_or_create(
                ingredient=ingredient['id'],
                recipe=instance.id
            )
            ingredient_recipe.amount = ingredient['amount']
            ingredient_recipe.save()

        list_tags = []
        for tag in tags:
            list_tags.append(Tag.objects.get(pk=tag))

        instance.tags.set(list_tags)
        instance.save()
        return instance


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

            recipes = []
            for recipe in Recipe.objects.filter(author=current_user.id):
                recipes.append(ShortRecipeSerializer(instance=recipe).data)

            data['recipes'] = recipes
            data['recipes_count'] = len(recipes)

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
