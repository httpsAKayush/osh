

import os
import sys
import django
import json
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
# from langchain_chroma import Chroma

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OpenSourceMadeEasy.settings')
django.setup()

from organizations.models import Project
from langchain_core.documents import Document

def fetch_project_tech_topics():
    projects = Project.objects.prefetch_related('technologies', 'topics').all()
    project_tech_topic_data = []
    for project in projects:
        tech_names = [tech.name for tech in project.technologies.all()]
        topic_names = [topic.name for topic in project.topics.all()]
        
        project_data = {
            'project_id': project.id,
            'techstack': tech_names,
            'topics': topic_names
        }
        
        project_tech_topic_data.append(
            Document(
                page_content=json.dumps(project_data), 
                metadata={"project_id": str(project.id)}
            )
        )
    
        
    return project_tech_topic_data


def fetch_specific_project(project_id):
    """
    Fetch techstack and topics for a specific project
    """
    try:
        project = Project.objects.prefetch_related('technologies', 'topics').get(id=project_id)
        
        return {
            'project_id': project.id,
            'techstack': [tech.name for tech in project.technologies.all()],
            'topics': [topic.name for topic in project.topics.all()]
        }
    except Project.DoesNotExist:
        return None


# all_projects = fetch_project_tech_topics()
# print(f"\n📊 Total projects: {len(all_projects)}")

# all_docs = all_projects
# print(all_docs)
# vectorstore = Chroma.from_documents(
#     all_docs,
#     embedding=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
#     persist_directory="project_vector_store"
# )

vector_presist=Chroma(
    persist_directory="project_vector_store",
    embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
)
