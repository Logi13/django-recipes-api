import datetime

from django.db import models
from django.utils import timezone

from django.contrib.auth.models import User

class Cuisine(models.Model):
    def __str__(self) -> str:
        return self.name
    
    name = models.CharField(max_length=50, default="None")

    class Meta:
        ordering = ['name']

class Recipe(models.Model):
    def __str__(self) -> str:
        return self.title
    
    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)
    
    title = models.CharField(max_length=50)
    description = models.TextField()
    ingredients = models.TextField()
    created_at = models.DateTimeField("date published", auto_now_add=True)
    cuisine = models.ForeignKey(Cuisine, on_delete=models.CASCADE, related_name="cuisine", blank=True, default=1)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipe_author", blank=True, default=1) # if we want the user to be able to post anonymously we would have an anon user to assign the comments to

class Comment(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField("date published", auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comment_author", blank=True, default=1)
    recipePost = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="recipe", blank=True, default=1)