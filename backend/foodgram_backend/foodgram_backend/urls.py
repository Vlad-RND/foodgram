from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from alone_app.views import (TagViewSet, IngredientViewSet, RecipeViewSet,
                             SubscriptionViewSet, FoodgramUserViewSet,
                             FavoritesViewSet, ShoppingListViewSet,)

router = routers.DefaultRouter()

router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes/(?P<recipe_id>\d+)/favorite',
                FavoritesViewSet,
                basename='favorite')
router.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart',
                ShoppingListViewSet,
                basename='shopping_cart')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'users/subscriptions',
                SubscriptionViewSet,
                basename='subscriptions')
router.register(r'users', FoodgramUserViewSet, basename='users')
router.register(r'users/(?P<user_id>\d+)/subscribe',
                SubscriptionViewSet,
                basename='subscribe')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/', include('djoser.urls')),  # Работа с пользователями
    path('api/auth/', include('djoser.urls.authtoken')),  # Работа с токенами
]
