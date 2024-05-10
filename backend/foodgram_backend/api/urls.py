from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()

router.register(r'tags', views.TagViewSet)
router.register(r'ingredients', views.IngredientViewSet, basename='ingredient')
router.register(r'recipes', views.RecipeViewSet, basename='recipes')
router.register(r'users', views.FoodgramUserViewSet, basename='users')


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
