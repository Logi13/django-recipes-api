from django.urls import path, re_path

from . import views

app_name = "recipes"
urlpatterns = [
    path("", views.index, name="index"),
    path("recipe/<int:recipeId>/", views.recipe, name="recipe"),
    path("cuisine/<int:cuisineId>/", views.cuisine, name="cuisine"),

    # get endpoints
    path("api/", views.index_api, name="index_api"),
    path("api/recipes/", views.recipe, name="get_recipes"),
    path("api/cuisines/", views.cuisine, name="get_cuisines"),
    path("api/recipe/<int:recipeId>/", views.recipe_api, name="recipe_api"),
    path("api/cuisine/<int:cuisineId>/", views.cuisine_api, name="cuicine_api"),

    # post endpoints
    path("api/recipe/", views.create_new_recipe, name="create_recipe"),
    path("api/cuisine/", views.create_new_cuisine, name="create_cuisine")
]