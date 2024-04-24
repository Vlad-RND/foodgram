from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from alone_app import views

router = routers.DefaultRouter()

router.register(r'tags', views.TagViewSet)
router.register(r'ingredients', views.IngredientViewSet, basename='ingredient')
router.register(r'recipes/(?P<recipe_id>\d+)/favorite',
                views.FavoritesViewSet,
                basename='favorite')
router.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart',
                views.ShoppingListViewSet,
                basename='shopping_cart')
router.register(r'recipes', views.RecipeViewSet, basename='recipes')
router.register(r'users/subscriptions',
                views.SubscriptionViewSet,
                basename='subscriptions')
router.register(r'users', views.FoodgramUserViewSet, basename='users')
router.register(r'users/(?P<user_id>\d+)/subscribe',
                views.SubscriptionViewSet,
                basename='subscribe')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/', include('djoser.urls')),  # Работа с пользователями
    path('api/auth/', include('djoser.urls.authtoken')),  # Работа с токенами
]
