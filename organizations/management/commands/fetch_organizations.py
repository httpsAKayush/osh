import httpx
from django.core.management.base import BaseCommand, CommandError
from organizations.models import Organization, Program, Mentor, Project
from techstack.models import Technology, Topic


class GsocOrgApiClient:
    def __init__(self):
        self.base_url = "https://api.gsocorganizations.dev"

    def get_all_organizations(self, year):
        response = httpx.get(f"{self.base_url}/{year}.json")
        response.raise_for_status()
        return response.json()


class GsocProjectApiClient:
    def __init__(self, project_id, year):
        self.base_url = f"https://summerofcode.withgoogle.com/api/projects/{project_id}/?role=&program_slug={year}"

    def get_project_data(self):
        response = httpx.get(self.base_url)
        response.raise_for_status()
        return response.json()


class Command(BaseCommand):
    help = 'Populate organizations and projects from GSOC API for a given year'

    def add_arguments(self, parser):
        parser.add_argument(
            'year',
            type=int,
            help='GSOC program year (e.g., 2024)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of organizations to process (useful for testing)'
        )

    def handle(self, *args, **options):
        year = options['year']
        limit = options.get('limit')
        
        self.stdout.write(self.style.WARNING(f'Starting to populate organizations for year {year}...'))
        
        try:
            org_client = GsocOrgApiClient()
            data = org_client.get_all_organizations(year)
            organizations = data['organizations']
            
            if limit:
                organizations = organizations[:limit]
                self.stdout.write(self.style.WARNING(f'Processing only {limit} organizations (limited)'))
            
            total_orgs = len(organizations)
            self.stdout.write(f'Found {total_orgs} organizations to process')
            
            for idx, org_data in enumerate(organizations, 1):
                self.stdout.write(f'\n[{idx}/{total_orgs}] Processing: {org_data["name"]}')
                
                org, created = Organization.objects.get_or_create(
                    slug=org_data['projects_url'].rstrip("/").split("/")[-1],
                    defaults={
                        'name': org_data['name'],
                        'description': org_data['description'],
                        'website_url': org_data['url'],
                        'projects_url': org_data['projects_url'],
                        'contact_email': org_data.get('contact_email', '')
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created organization: {org.name}'))
                else:
                    self.stdout.write(f'  → Organization already exists: {org.name}')
                
                # Add topics
                for topic_name in org_data.get('topics', []):
                    if isinstance(topic_name, str) and ',' in topic_name:
                        topic_names = [name.strip() for name in topic_name.split(',') if name.strip()]
                        for individual_topic in topic_names:
                            topic, _ = Topic.objects.get_or_create(name=individual_topic)
                            org.topics.add(topic)
                    else:
                        topic, _ = Topic.objects.get_or_create(name=topic_name)
                        org.topics.add(topic)
                
                # Add technologies
                for tech_name in org_data.get('technologies', []):
                    if isinstance(tech_name, str) and ',' in tech_name:
                        tech_names = [name.strip() for name in tech_name.split(',') if name.strip()]
                        for individual_tech in tech_names:
                            tech, _ = Technology.objects.get_or_create(name=individual_tech)
                            org.technologies.add(tech)
                    else:
                        tech, _ = Technology.objects.get_or_create(name=tech_name)
                        org.technologies.add(tech)
                
                # Process projects
                projects = org_data.get('projects', [])
                self.stdout.write(f'  Processing {len(projects)} projects...')
                
                for proj_idx, project_data in enumerate(projects, 1):
                    try:
                        url = project_data['project_url']
                        parts = url.rstrip("/").split("/")
                        proj_year = parts[-3]
                        project_id = parts[-1]
                        
                        proj_client = GsocProjectApiClient(project_id, proj_year)
                        detailed_project_data = proj_client.get_project_data()
                        
                        if detailed_project_data:
                            req_data = detailed_project_data['entities']['projects'][0]
                            
                           
                            org = Organization.objects.get(slug=req_data['organization_slug'])
                            
                           
                            prog_data = detailed_project_data['entities']['programs'][0]
                            program, _ = Program.objects.get_or_create(
                                name=prog_data['name'],
                                year=int(prog_data['slug'])
                            )
                            
                            
                            project, proj_created = Project.objects.get_or_create(
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
                            
                            if proj_created:
                                self.stdout.write(f'    ✓ [{proj_idx}/{len(projects)}] Created project: {project.title[:50]}...')
                            
                            
                            for topic_name in req_data['topic_tags']:
                                if isinstance(topic_name, str) and ',' in topic_name:
                                    topic_names = [name.strip() for name in topic_name.split(',') if name.strip()]
                                    for individual_topic in topic_names:
                                        topic, _ = Topic.objects.get_or_create(name=individual_topic)
                                        project.topics.add(topic)
                                else:
                                    topic, _ = Topic.objects.get_or_create(name=topic_name)
                                    project.topics.add(topic)
                            
                            
                            for tech_name in req_data['tech_tags']:
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
                            
                            project.save()
                    
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'    ✗ Error processing project: {str(e)}'))
                        continue
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully updated organizations and projects for {year}!'))
            
        except Exception as e:
            raise CommandError(f'Error populating organizations: {str(e)}')