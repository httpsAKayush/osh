import os
import sys
import httpx
from urllib.parse import urlparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OpenSourceMadeEasy.settings')
import django
django.setup()
from organizations.models import Organization, Program, Mentor, Project
from techstack.models import Technology, Topic
class GsocOrgApiClient:
    def __init__(self):
        self.base_url = "https://api.gsocorganizations.dev"

    def get_all_organizations(self,year):
        response = httpx.get(f"{self.base_url}/{year}.json")
        response.raise_for_status()
        return response.json()
    
class GsocProjectApiClient:
    def __init__(self,project_id,year):
        self.base_url = f"https://summerofcode.withgoogle.com/api/projects/{project_id}/?role=&program_slug={year}"

    def get_project_data(self):
        response = httpx.get(self.base_url)
        response.raise_for_status()
        return response.json()
    
def populate_organizations(year):
    org_client = GsocOrgApiClient()
    data = org_client.get_all_organizations(year)
    response=data['organizations'][0:2]
    for org_data in response:
        org,created = Organization.objects.get_or_create(
            slug=org_data['projects_url'].rstrip("/").split("/")[-1],
            defaults={
                'name': org_data['name'],
                'description': org_data['description'],
                'website_url': org_data['url'],
                'projects_url': org_data['projects_url'],
                'contact_email': org_data.get('contact_email', '')
            }
        )
        for topic_name in org_data.get('topics', []):
            # Split comma-separated topics and clean them
            if isinstance(topic_name, str) and ',' in topic_name:
                topic_names = [name.strip() for name in topic_name.split(',') if name.strip()]
                for individual_topic in topic_names:
                    topic, _ = Topic.objects.get_or_create(name=individual_topic)
                    org.topics.add(topic)
            else:
                topic, _ = Topic.objects.get_or_create(name=topic_name)
                org.topics.add(topic)

        for tech_name in org_data.get('technologies', []):
            # Split comma-separated technologies and clean them
            if isinstance(tech_name, str) and ',' in tech_name:
                tech_names = [name.strip() for name in tech_name.split(',') if name.strip()]
                for individual_tech in tech_names:
                    tech, _ = Technology.objects.get_or_create(name=individual_tech)
                    org.technologies.add(tech)
            else:
                tech, _ = Technology.objects.get_or_create(name=tech_name)
                org.technologies.add(tech)
        
        projects=org_data.get('projects', [])
        for project_data in projects:
            url=project_data['project_url']
            parts = url.rstrip("/").split("/")  
            year = parts[-3]        
            project_id = parts[-1] 
            proj_client=GsocProjectApiClient(project_id,year)
            detailed_project_data=proj_client.get_project_data()
            if detailed_project_data:
                req_data=detailed_project_data['entities']['projects'][0]
                org=Organization.objects.get(slug=req_data['organization_slug'])
                prog_data = detailed_project_data['entities']['programs'][0]
                program, _ = Program.objects.get_or_create(name=prog_data['name'], year=int(prog_data['slug']))
                project, _ = Project.objects.get_or_create(
                    id=req_data['uid'],
                    defaults={
                        'title': req_data['title'],
                        'short_description': req_data['body'],
                        'status': req_data['status'],
                        'project_code_url': req_data['project_code_url'],
                        'organization': org,
                        'program': program
                    }
                )
                for topic_name in req_data['topic_tags']:
                    # Split comma-separated topics and clean them
                    if isinstance(topic_name, str) and ',' in topic_name:
                        topic_names = [name.strip() for name in topic_name.split(',') if name.strip()]
                        for individual_topic in topic_names:
                            topic, _ = Topic.objects.get_or_create(name=individual_topic)
                            project.topics.add(topic)
                    else:
                        topic, _ = Topic.objects.get_or_create(name=topic_name)
                        project.topics.add(topic)

                for tech_name in req_data['tech_tags']:
                    # Split comma-separated technologies and clean them
                    if isinstance(tech_name, str) and ',' in tech_name:
                        tech_names = [name.strip() for name in tech_name.split(',') if name.strip()]
                        for individual_tech in tech_names:
                            tech, _ = Technology.objects.get_or_create(name=individual_tech)
                            project.technologies.add(tech)
                    else:
                        tech, _ = Technology.objects.get_or_create(name=tech_name)
                        project.technologies.add(tech)
                
                for mentor_name in req_data.get('assigned_mentors', []):
                    mentor, _ = Mentor.objects.get_or_create(name=mentor_name)
                    project.mentors.add(mentor)
                prog_data=detailed_project_data['entities']['programs'][0]
                program, _ = Program.objects.get_or_create(name=prog_data['name'], year=int(prog_data['slug']))
                project.program=program
                project.save()
    print(f"✅ Trial Organizations and Projects and Projects for {year} loaded!")
populate_organizations(2024)