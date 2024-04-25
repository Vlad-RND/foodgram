from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

from .constants import (COLOR_HEX_LIMIT, EMAIL_LIMIT,
                        SHORT_NAME_LEN, TITLE_STR_LIMIT,
                        NAME_STR_LIMIT)


class NameModel(models.Model):
    """Абстрактная модель для добавления поля name."""

    name = models.CharField(
        'Название',
        unique=True,
        max_length=TITLE_STR_LIMIT,
    )

    class Meta:
        abstract = True
        ordering = ('name',)


class FoodgramUser(AbstractUser):
    """Расширенная модель пользователя."""

    username = models.CharField(
        max_length=NAME_STR_LIMIT,
        verbose_name='Имя пользователя',
        unique=True,
        validators=[
            RegexValidator(regex=r'^[\w.@+-]+$', message='Неподходящее имя')
        ],
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
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username


class Tag(NameModel):
    """Модель тега."""

    color = models.CharField(
        'Цвет тега',
        max_length=COLOR_HEX_LIMIT,
        help_text='Цвет в кодировке HEX.'
    )
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


class Ingredient(models.Model):
    """Модель ингридиента."""

    name = models.CharField('Наименование', max_length=TITLE_STR_LIMIT,)

    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=TITLE_STR_LIMIT,
    )

    class Meta:
        verbose_name = 'ингридиент'
        verbose_name_plural = 'Ингридиенты'

        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

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
        # upload_to='alone_app/images/',
        upload_to='media',
    )
    text = models.TextField('Описание',)
    cooking_time = models.IntegerField('Время приготовления, мин',)
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        auto_now_add=True
    )
    tags = models.ManyToManyField(
        Tag, through='TagRecipe', verbose_name='Теги',
    )

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

    def __str__(self):
        return self.name[:SHORT_NAME_LEN]


class TagRecipe(models.Model):
    """Связующая модель тега и рецепта."""

    tag = models.ForeignKey(
        Tag,
        related_name='tag_recipe',
        on_delete=models.CASCADE,
        verbose_name='Тег',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='tag_recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'тег рецепта'
        verbose_name_plural = 'Теги рецептов'

    def __str__(self):
        return f'{self.tag} {self.recipe}'


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
    amount = models.IntegerField('Количество')

    class Meta:
        verbose_name = 'ингридиент рецепта'
        verbose_name_plural = 'Ингридиенты рецептов'

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class Subscription(models.Model):
    """Модель подписки."""

    base_user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='base_user',
        verbose_name='Подписывающийся',
    )
    follow_user = models.ForeignKey(
        FoodgramUser,
        related_name='follow_user',
        on_delete=models.CASCADE,
        verbose_name='На кого подписаться',
        blank=True,
    )


class Favorites(models.Model):
    """Модель списка избранного."""

    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='user',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт',
    )


class ShoppingList(models.Model):
    """Модель списка покупок."""

    customer = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='customer',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='buy_recipe',
        verbose_name='Рецепт',
    )
