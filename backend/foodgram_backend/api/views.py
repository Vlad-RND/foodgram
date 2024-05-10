from http import HTTPStatus

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
            return (IsAuthenticated(),)
        return super().get_permissions()

    @ action(
        methods=('GET', ),
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        return self.get_paginated_response(
            GetSubscriptionSerializer(
                self.paginate_queryset(
                    FoodgramUser.objects.filter(
                        author__follower=request.user
                    ).annotate(
                        recipes_count=Count('recipes')
                    )
                ),
                many=True,
                context={'request': request}
            ).data
        )

    @ action(
        methods=('POST', ),
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
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @ subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        subscription = Subscription.objects.filter(
            follower=self.request.user.id,
            author=id
        )

        if not subscription.exists():
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        subscription.delete()

        return HttpResponse(status=HTTPStatus.NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение информация о Тегах."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ('get', )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
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
    def write_object(serializer_class, pk, request):
        data = {
            'user': request.user.id,
            'recipe': pk
        }
        serializer = serializer_class(
            data=data, context={'request': request, })

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @ action(
        methods=('POST', ),
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        return self.write_object(FavoritesSerializer, pk, request)

    @ favorite.mapping.delete
    def delete_favorite(self, request, pk):
        favorite = Favorites.objects.filter(
            user=self.request.user.id,
            recipe=pk
        )
        if not favorite.exists():
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        favorite.delete()

        return HttpResponse(status=HTTPStatus.NO_CONTENT)

    @ action(
        methods=('POST', ),
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        return self.write_object(ShoppingListSerializer, pk, request)

    @ shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        shopping_cart = ShoppingList.objects.filter(
            user=self.request.user.id,
            recipe=pk
        )
        if not shopping_cart.exists():
            return HttpResponse(status=400)

        shopping_cart.delete()

        return HttpResponse(status=204)

    @ action(
        detail=False,
        methods=('GET', ),
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
