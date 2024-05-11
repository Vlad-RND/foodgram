from colorfield.fields import ColorField
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import (RegexValidator, MinValueValidator,
                                    MaxValueValidator)
from django.core.exceptions import ValidationError

from .constants import (EMAIL_LIMIT, NAME_STR_LIMIT,
                        SHORT_NAME_LEN, TITLE_STR_LIMIT,
                        MIN_VALUE, MAX_VALUE)


class NameModel(models.Model):
    """Абстрактная модель для добавления поля name."""

    name = models.CharField(
        'Название',
        max_length=TITLE_STR_LIMIT,
    )

    class Meta:
        abstract = True
        ordering = ('name',)


class FoodgramUser(AbstractUser):
    """Расширенная модель пользователя."""

    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')
    USERNAME_FIELD = 'email'
    username = models.CharField(
        max_length=NAME_STR_LIMIT,
        verbose_name='Имя пользователя',
        unique=True,
        validators=(
            RegexValidator(regex=r'^[\w.@+-]+$', message='Неподходящее имя'),
        ),
    )
    email = models.EmailField(
        max_length=EMAIL_LIMIT,
        verbose_name='email',
        unique=True,
    )
    first_name = models.CharField(
        max_length=NAME_STR_LIMIT,
        verbose_name='имя',
    )
    last_name = models.CharField(
        max_length=NAME_STR_LIMIT,
        verbose_name='фамилия',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username', 'first_name',)

    def __str__(self):
        return self.username


class Tag(NameModel):
    """Модель тега."""

    color = ColorField('Цвет тега',)
    slug = models.CharField(
        'Идентификатор',
        unique=True,
        help_text='Идентификатор страницы для URL;'
        ' разрешены символы латиницы, цифры, дефис и подчёркивание.',
        max_length=TITLE_STR_LIMIT,
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:SHORT_NAME_LEN]


class Ingredient(NameModel):
    """Модель ингридиента."""

    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=TITLE_STR_LIMIT,
    )

    class Meta:
        verbose_name = 'ингридиент'
        verbose_name_plural = 'Ингридиенты'

        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient'
            ),
        )

    def __str__(self):
        return self.name[:SHORT_NAME_LEN]


class Recipe(NameModel):
    """Модель рецепта."""

    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
    )
    image = models.ImageField(
        'Изображение',
        upload_to='',
    )
    text = models.TextField('Описание',)
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления, мин',
        validators=(
            MinValueValidator(MIN_VALUE, message=f'Минимум - {MIN_VALUE}.'),
            MaxValueValidator(MAX_VALUE, message=f'Максимум - {MAX_VALUE}.'),
        ),
    )
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        auto_now_add=True
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги',)

    ingredients = models.ManyToManyField(
        Ingredient,
        through='ingredientRecipe',
        verbose_name='Ингридиенты',
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        default_related_name = 'recipes'
        constraints = (
            models.UniqueConstraint(
                fields=('name', ),
                name='unique_name'
            ),
        )

    def __str__(self):
        return self.name[:SHORT_NAME_LEN]


class IngredientRecipe(models.Model):
    """Связующая модель ингридиента и рецепта."""

    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredient_recipe',
        on_delete=models.CASCADE,
        verbose_name='Ингридиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='ingredient_recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(
            MinValueValidator(MIN_VALUE, message=f'Минимум - {MIN_VALUE}.'),
            MaxValueValidator(MAX_VALUE, message=f'Максимум - {MAX_VALUE}.'),
        ),
    )

    class Meta:
        verbose_name = 'ингридиент рецепта'
        verbose_name_plural = 'Ингридиенты рецептов'
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredient_recipe'
            ),
        )

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class Subscription(models.Model):
    """Модель подписки."""

    follower = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь',
    )
    author = models.ForeignKey(
        FoodgramUser,
        related_name='author',
        on_delete=models.CASCADE,
        verbose_name='Подписка',
        blank=True,
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('follower', 'author'),
                name='unique_subscription'
            ),
        )

    def clean(self):
        if self.follower == self.author:
            raise ValidationError("Нельзя подписываться на самого себя.")
        super().save(self)

    def __str__(self):
        return f'Подписка {self.follower} на {self.author}'


class UserRecipeModel(models.Model):
    """Абстрактная модель для добавления полей user и recipe."""

    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        ordering = ('user',)

    def __str__(self):
        return (f'Рецепт {self.recipe} в '
                f'{self._meta.verbose_name} у {self.user}')


class Favorites(UserRecipeModel):
    """Модель списка избранного."""

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранные'
        default_related_name = 'favorites'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorites'
            ),
        )


class ShoppingList(UserRecipeModel):
    """Модель списка покупок."""

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_list'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_list'
            ),
        )
