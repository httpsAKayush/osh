from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    github_username=models.CharField(max_length=255,blank=False,null=False)
    linkedin_profile_url=models.URLField(max_length=255,blank=True,null=True)
    skills=models.ManyToManyField(
        'Skill',
        related_name='users'
    )
    def __str__(self):
        return self.username

class Skill(models.Model):
    skill_name=models.CharField(max_length=255,blank=False,null=False,unique=True)
    skill_type=models.CharField(max_length=255,blank=False,null=False)
    def __str__(self):
        return self.skill_name
