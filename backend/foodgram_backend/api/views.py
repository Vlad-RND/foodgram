from django.http import HttpResponse, FileResponse
from django.db.models import Sum, Count
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.pagination import PageNumberPagination

from .filterset import RecipeFilter, IngredientFilter
from recipes.models import (Tag, Ingredient, Recipe, FoodgramUser,
                            Subscription, Favorites, ShoppingList,
                            IngredientRecipe)
from .permissions import IsAuthorOrReadOnly
from .serializers import (TagSerializer, IngredientSerializer,
                          CreateRecipeSerializer, GetSubscriptionSerializer,
                          ShowRecipeSerializer, FavoritesSerializer,
                          ShoppingListSerializer, CreateSubscriptionSerializer)


class FoodgramUserViewSet(UserViewSet):
    """Получение информация о пользователе."""

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    @ action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        return self.get_paginated_response(
            GetSubscriptionSerializer(
                self.paginate_queryset(
                    FoodgramUser.objects.all().annotate(
                        recipes_count=Count('recipes')
                    )
                ),
                many=True,
                context={'request': request}
            ).data
        )

    @ action(
        methods=['POST'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        data = {
            'follower': request.user.id,
            'author': id
        }
        serializer = CreateSubscriptionSerializer(
            data=data, context={'request': request, })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

    @ subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        if not Subscription.objects.filter(
            follower=self.request.user.id,
            author=id
        ).exists():
            return HttpResponse(status=400)

        Subscription.objects.get(
            follower=self.request.user.id,
            author=id
        ).delete()

        return HttpResponse(status=204)


class TagViewSet(mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    """Получение информация о Тегах."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ('get', )
    pagination_class = None


class IngredientViewSet(mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """Получение информация об Ингредиентах."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    http_method_names = ('get', )
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Набор представлений Рецепта."""

    queryset = Recipe.objects.all().select_related(
        'author'
    ).prefetch_related('tags', 'ingredients')
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ShowRecipeSerializer
        return CreateRecipeSerializer

    @staticmethod
    def write(serializer_class, pk, request):
        data = {
            'user': request.user.id,
            'recipe': pk
        }
        serializer = serializer_class(
            data=data, context={'request': request, })

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

    @ action(
        methods=['POST'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        return self.write(FavoritesSerializer, pk, request)

    @ favorite.mapping.delete
    def delete_favorite(self, request, pk):
        if not Favorites.objects.filter(
            user=self.request.user.id,
            recipe=pk
        ).exists():
            return HttpResponse(status=400)

        Favorites.objects.get(
            user=self.request.user,
            recipe=pk
        ).delete()

        return HttpResponse(status=204)

    @ action(
        methods=['POST'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        return self.write(ShoppingListSerializer, pk, request)

    @ shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        if not ShoppingList.objects.filter(
            user=self.request.user.id,
            recipe=pk
        ).exists():
            return HttpResponse(status=400)

        ShoppingList.objects.get(
            user=self.request.user,
            recipe=pk
        ).delete()

        return HttpResponse(status=204)

    @ action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Функция для получения файла со списком покупок."""

        data = IngredientRecipe.objects.filter(
            recipe__shopping_list__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            amount=Sum('amount')
        ).order_by('ingredient__name')

        answer = ''
        for item in data:
            name, unit, amount = item.values()
            answer += f'{name}, {unit}: {amount}\n'

        return FileResponse(
            answer,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain'
        )


class SubscriptionViewSet(mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    """Набор представлений Подписки."""

    queryset = Subscription.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = GetSubscriptionSerializer
