from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.http import HttpResponse, Http404, JsonResponse
from django.core import serializers
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt

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
'''
getAllRecipeData() -> returns Recipe as a querySet
might be worth to check Celery for asynchronous operations
@TODO expand to accomodate more complex queries, using ex. select_related('author') for the recipe and post,etc
@TODO have a look to abstract and make derived classes from base as operations are pretty much the same and it might be more clean

'''
class FetchDataFromDB():
    data = []
    data_querySet = None
    dataType: Union[Recipe, Cuisine] = None
    cacheString = "None"
    request = None
    op = "None"
    parameter = None

    def __init__(self, dataType: Union[Recipe, Cuisine], cacheString: str, operation = "None", parameter = None) -> None:
        self.data = []
        self.dataType = globals()[dataType]
        self.cacheString = cacheString
        self.op = operation
        self.parameter = parameter

    def run(self) -> Union[Recipe, Cuisine]:
        if allow_caching:
            self.data = self.saveDataIfExistsInCache()
        
        if len(self.data) == 0:
            self.getDataFromDb()
    
    def saveDataIfExistsInCache(self) -> None:
        self.data_querySet = cache.get(self.cacheString)

    def saveDataToCache(self) -> None:
        cache.set(self.cacheString, self.data, 30*60)

    def getDataFromDb(self) -> None:
        print(self.op)
        if self.op == "getAllRecipes" or self.op == "getAllCuisines" or self.op == "None" :
            self.data_querySet = self.dataType.objects.all() # add support o select only columns that are useful
            print(self.data_querySet)
        elif self.op == "filterById":
            self.data = self.dataType.objects.filter(id=self.parameter).first()
        elif self.op == "filterByCuisine":
            self.data_querySet = self.dataType.objects.filter(cuisine=self.parameter)
        elif self.op == "getById":
            self.data = self.dataType.objects.get(self.parameter)

    '''
    If the values are a query set we need to evaluate the data
    There are cases that the data might be too big and inneficient to load in memory
    @TODO make sure to have a way to load data from a queryset when all is asked (pagination?)
    '''
    def evaluateQuerySet(self):
        for entry in self.data_querySet.iterator():
            self.data.append(entry)
        self.saveDataToCache()

def getAllRecipeData(): # Note: Note 100% sure if this should have Recipe return type since it is a query set
    dataFetcher = FetchDataFromDB("Recipe", "all_recipes_data", "getAllRecipes")
    dataFetcher.run()
    dataFetcher.evaluateQuerySet()
    return dataFetcher.data

def getAllCuisineData():
    dataFetcher = FetchDataFromDB("Cuisine", "all_cuisines_data", "getAllCuisines")
    dataFetcher.run()
    dataFetcher.evaluateQuerySet()
    return dataFetcher.data

def getCuisineById(cuisineId) -> Cuisine:
    dataFetcher = FetchDataFromDB("Cuisine", f'cuisine_{cuisineId}_data', "filterById", cuisineId)
    dataFetcher.run()
    return dataFetcher.data

def getRecipeById(recipeId) -> Recipe:
    dataFetcher = FetchDataFromDB("Recipe", f'recipe_{recipeId}_data', "filterById", recipeId)
    dataFetcher.run()
    return dataFetcher.data

def getRecipesByCuisine(cuisine, cuisineId):
    dataFetcher = FetchDataFromDB("Recipe", f'cuisineId_{cuisineId}_recipe_data', "filterByCuisine", cuisine)
    dataFetcher.run()
    return dataFetcher.data

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
            "name": cuisine.name
        }
    except Recipe.DoesNotExist:
        raise Http404("Cusine does not exist")
    
    return JsonResponse(cuisine_data, content_type='application/json')

@csrf_exempt
def create_new_recipe(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            jsonschema.validate(data, recipeValidation())

            cuisine = getCuisineById(data["cuisine"])
            if cuisine is None:
                response_data = {'error': 'Json not correct, validation error'}
                return JsonResponse(response_data, status=400)
            
            instance = Recipe.objects.create(title=data["title"], description=data["description"], ingredients=data["ingredients"], cuisine=cuisine)
            instance.save()
            response_data = {'message': 'Data received and processed successfully'}
            return JsonResponse(response_data)
        except jsonschema.ValidationError:
            response_data = {'error': 'Json not correct, validation error'}
            return JsonResponse(response_data, status=400)
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
            response_data = {'message': 'Data received and processed successfully'}
            return JsonResponse(response_data)
        except jsonschema.ValidationError:
            response_data = {'error': 'Json not correct, validation error'}
            return JsonResponse(response_data, status=400)
    else:
        response_data = {'error': 'Method not allowed'}
        return JsonResponse(response_data, status=405)

