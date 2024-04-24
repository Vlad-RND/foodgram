from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated


from .filterset import RecipeFilter
from .models import (Tag, Ingredient, Recipe, FoodgramUser,
                     Subscription, Favorites, ShoppingList,
                     IngredientRecipe)
from .permissions import IsAuthorOrReadOnly
from .serializers import (TagSerializer, IngredientSerializer,
                          CreateRecipeSerializer, SubscriptionSerializer,
                          ShowRecipeSerializer, FavoritesSerializer,
                          ShoppingListSerializer)


class PermissionMixin(mixins.CreateModelMixin, mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)


class FoodgramUserViewSet(UserViewSet):
    """Получение информация о пользователе."""

    @action(
        detail=False,
        methods=['GET', 'PUT'],
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, is_subscribed=False, *args, **kwargs)


class TagViewSet(viewsets.ModelViewSet):
    """Получение информация о Тегах."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get',]
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Получение информация об Ингредиентах."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    http_method_names = ['get',]
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Набор представлений Рецепта."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateRecipeSerializer
        elif self.request.method == "PATCH":
            return CreateRecipeSerializer
        else:
            return ShowRecipeSerializer

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Функция для получения файла со списком покупок."""
        responce = HttpResponse(content_type='text/plain')
        responce['Content-Disposition'] = 'attachment; filename=shopping_list.txt'

        data = {}
        for list in ShoppingList.objects.filter(customer=request.user):
            for item in IngredientRecipe.objects.filter(recipe=list.recipe):
                ingredient = item.ingredient.name
                if ingredient in data:
                    data[ingredient] += item.amount
                else:
                    data[ingredient] = item.amount

        for key, value in data.items():
            responce.writelines(f'{key}: {value}\n')

        return responce


class SubscriptionViewSet(PermissionMixin):
    """Набор представлений Подписки."""

    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    @action(methods=['delete'], detail=False)
    def delete(self, request, user_id,):

        if not FoodgramUser.objects.filter(pk=user_id):
            return HttpResponse(status=404)

        if not Subscription.objects.filter(
            base_user=self.request.user.id,
            follow_user=user_id
        ).exists():
            return HttpResponse(status=400)

        Subscription.objects.get(
            base_user=self.request.user,
            follow_user=user_id
        ).delete()

        return HttpResponse(status=204)

    def perform_create(self, serializer):
        serializer.save(base_user=self.request.user)


class FavoritesViewSet(PermissionMixin):

    """Набор представлений Избранного."""

    queryset = Favorites.objects.all()
    serializer_class = FavoritesSerializer

    @action(methods=['delete'], detail=False)
    def delete(self, request, recipe_id,):

        if not Recipe.objects.filter(pk=recipe_id):
            return HttpResponse(status=404)

        if not Favorites.objects.filter(
            user=self.request.user.id,
            recipe=recipe_id
        ).exists():
            return HttpResponse(status=400)

        Favorites.objects.get(
            user=self.request.user,
            recipe=recipe_id
        ).delete()

        return HttpResponse(status=204)

    def get_queryset(self):
        return self.request.user.user

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ShoppingListViewSet(PermissionMixin):
    """Создание и удаление Списка покупок."""

    queryset = ShoppingList.objects.all()
    serializer_class = ShoppingListSerializer

    @action(methods=['delete'], detail=False)
    def delete(self, request, recipe_id):

        if not Recipe.objects.filter(pk=recipe_id):
            return HttpResponse(status=404)

        if not ShoppingList.objects.filter(
            customer=self.request.user.id,
            recipe=recipe_id
        ).exists():
            return HttpResponse(status=400)

        ShoppingList.objects.get(
            customer=self.request.user,
            recipe=recipe_id
        ).delete()

        return HttpResponse(status=204)

    def get_queryset(self):
        return self.request.user.user

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
