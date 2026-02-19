from django.contrib import admin

# Register your models here.
from users.models import User,Skill
from organizations.models import Organization,Program,Mentor,Project
from projects.models import ProjectRequirement
from techstack.models import Technology,Topic

admin.site.register(User)
admin.site.register(Skill)
admin.site.register(Organization)
admin.site.register(Program)
admin.site.register(Mentor)
admin.site.register(Project)
admin.site.register(ProjectRequirement)
admin.site.register(Technology)
admin.site.register(Topic)