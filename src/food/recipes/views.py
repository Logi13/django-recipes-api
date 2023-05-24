from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.http import HttpResponse, Http404, JsonResponse
from django.core import serializers
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt

from django.db.models import F

from django.db import transaction

from typing import Union
import threading
import json
import jsonschema
from pydoc import locate


from food.settings import allow_caching

from .models import Cuisine, Recipe
from .validators import recipeValidation, cuisineValidation

#www.themealdb.com/api/json/v1/1/filter.php?a=Italian


# ----------------- Start Helpers -----------------

def getAllRecipeData(): # Note: Note 100% sure if this should have Recipe return type since it is a query set
    return Recipe.objects.all()

def getAllCuisineData():
    return Cuisine.objects.all()

def getCuisineById(cuisineId) -> Cuisine:
    return Cuisine.objects.get(id=cuisineId)

def getRecipeById(recipeId) -> Recipe:
    return Cuisine.objects.get(id=recipeId)

def getRecipesByCuisine(cuisine, cuisineId):
    return Recipe.objects.get(cuisine)

# ----------------- End Helpers -----------------

def index(request):
    context = {"recipe_list": None}
    try:
        recipes = getAllRecipeData()
        cuisines = getAllCuisineData()

        context["recipe_list"] = recipes
        context["cuisine_list"] = cuisines
    except Cuisine.DoesNotExist:
        raise Http404("Recipes does not exist")
    
    return TemplateResponse(request, "mainpage/home.html", context, status=200)

def index_api(request):
    try:
        recipes_querySet = getAllRecipeData()
        cuisines_querySet = getAllCuisineData()

        recipes_serialized_data = serializers.serialize('json', recipes_querySet)
        cuisines_serialized_data = serializers.serialize('json', cuisines_querySet)
        data = {
            "recipes": recipes_serialized_data,
            "cuisines": cuisines_serialized_data
        }
    except Cuisine.DoesNotExist:
        raise Http404("Recipes does not exist")
    
    return HttpResponse(content=json.dumps(data), content_type='application/json')

def get_cuisine(request):
    cuisines_serialized_data = serializers.serialize('json', getAllCuisineData())
    return HttpResponse(content=json.dumps(cuisines_serialized_data), content_type='application/json')

def get_recipes(request):
    recipes_serialized_data = serializers.serialize('json', getAllRecipeData())
    return HttpResponse(content=json.dumps(recipes_serialized_data), content_type='application/json')

def recipe(request, recipeId):
    context = {}
    try:
        recipe = getRecipeById(recipeId)
        print(recipe)
        context = {"recipe": recipe}
    except Recipe.DoesNotExist:
        raise Http404("Recipe does not exist")
    return TemplateResponse(request, "mainpage/recipe.html", context, status=200)

def recipe_api(request, recipeId):
    try:
        recipe = getRecipeById(recipeId)
        recipe_data = {
            "id": recipe.id,
            "title": recipe.title,
            "description": recipe.description,
            "ingredients": recipe.ingredients,
            "created_at": recipe.created_at,
            "author": recipe.author.username
        }
    except Recipe.DoesNotExist:
        raise Http404("Recipe does not exist")
    
    return JsonResponse(recipe_data, content_type='application/json')

def cuisine(request, cuisineId):
    context = {}
    try:
        cuisine = getCuisineById(cuisineId)
        recipes = getRecipesByCuisine(cuisine, cuisineId)
        context = {"cuisine_recipe": recipes}
    except Cuisine.DoesNotExist:
        raise Http404("Recipe does not exist")
    return render(request, "mainpage/cuisine.html", context, status=200)

def cuisine_api(request, cuisineId):
    try:
        cuisine = getCuisineById(cuisineId)
        cuisine_data = {
            "id": cuisine.id,
            "name": cuisine.name
        }
    except Recipe.DoesNotExist:
        raise Http404("Cusine does not exist")
    
    return JsonResponse(cuisine_data, content_type='application/json')

@csrf_exempt
@transaction.non_atomic_requests
def create_new_recipe(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            jsonschema.validate(data, recipeValidation())

            cuisine = getCuisineById(data["cuisine"])
            instance = Recipe.objects.create(title=data["title"], description=data["description"], ingredients=data["ingredients"], cuisine=cuisine)
            instance.save()
            response_data = {'message': 'Data received and processed successfully'}
            return JsonResponse(response_data)
        except Cuisine.DoesNotExist:
            response_data = {'error': 'Cuisine does not exist'}
            return JsonResponse(response_data, status=400)
        except jsonschema.ValidationError:
            response_data = {'error': 'Json not correct, validation error'}
            return JsonResponse(response_data, status=400)
        except Exception as e:
            response_data = {'error': f'Something went very wrong! {e}'}
            return JsonResponse(response_data, status=500)
    else:
        response_data = {'error': 'Method not allowed'}
        return JsonResponse(response_data, status=405)

@csrf_exempt
def create_new_cuisine(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            jsonschema.validate(data, cuisineValidation())
            
            instance = Cuisine.objects.create(**data)
            instance.save()
            response_data = {'message': 'Data received and processed successfully.'}
            return JsonResponse(response_data)
        
        except jsonschema.ValidationError:
            response_data = {'error': 'Json not correct, validation error'}
            return JsonResponse(response_data, status=400)
    else:
        response_data = {'error': 'Method not allowed'}
        return JsonResponse(response_data, status=405)

