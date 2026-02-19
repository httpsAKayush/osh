from django.db import models
from techstack.models import Technology,Topic
import uuid
class Program(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)   
    year = models.IntegerField()              

    def __str__(self):
        return f"{self.name} ({self.year})"

class Mentor(models.Model):
    name = models.CharField(max_length=255)
    linkedin_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    projects_url=models.URLField()
    slug = models.CharField(max_length=100, unique=True, null=False)
    contact_email=models.EmailField(blank=True, null=True)
    topics = models.ManyToManyField(Topic, related_name="organizations", blank=True)
    technologies = models.ManyToManyField(Technology, related_name="organizations", blank=True)
    
    def __str__(self):
        return self.name
    
class Project(models.Model):
    id = models.CharField(primary_key=True, max_length=100)  
    title = models.CharField(max_length=255)
    short_description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="projects")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="projects")
    technologies = models.ManyToManyField(Technology, related_name="projects", blank=True)
    topics = models.ManyToManyField(Topic, related_name="projects", blank=True)
    mentors = models.ManyToManyField(Mentor, related_name="projects", blank=True)
    project_code_url=models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title


