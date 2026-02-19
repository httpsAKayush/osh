import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OpenSourceMadeEasy.settings')
import django
django.setup()
from techstack.models import Technology, Topic
try:
    from technologies import technologies
except ImportError:
    technologies = []
try:
    from topics import gsoc_topic_tags
except ImportError:
    gsoc_topic_tags = []

def populate_technologies_and_topics():
    for tech in technologies:
        Technology.objects.get_or_create(name=tech)
    for topic in gsoc_topic_tags:
        Topic.objects.get_or_create(name=topic)
    print("✅ Technologies and topics loaded!")

if __name__ == "__main__":
    populate_technologies_and_topics()