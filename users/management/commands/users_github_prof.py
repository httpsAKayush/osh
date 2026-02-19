from urllib import response
import httpx
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
Github_token=os.getenv("GITHUB_TOKEN")
api_key=os.getenv('GEMINI_API_KEY')
from pydantic import BaseModel
from typing import List, Dict, Any, Optional,Iterable,Tuple,Set

model=ChatGoogleGenerativeAI(
    api_key=api_key,
    model='gemini-2.5-flash'
)
class DependencyList(BaseModel):
    dependencies: List[str]

structured = model.with_structured_output(DependencyList)

class GithubClient:
    def __init__(self,token):
        self.base_url="https://api.github.com/"
        self.graphql_url="https://api.github.com/graphql"
        self.token = token

    def _headers(self):
        return{
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.token}"
        }
    
    def get_pinned_repos(self):
        """Get pinned repositories of the authenticated user using GitHub GraphQL API"""
        query = """
        query {
          viewer {
            login
            pinnedItems(first: 6, types: [REPOSITORY]) {
              nodes {
                ... on Repository {
                  name
                  url
                  description
                  languages(first: 10) {
                    nodes {
                      ... on Language {
                        name
                      }
                    }
                  }
                  repositoryTopics(first: 10) {
                    nodes {
                      topic {
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        response = httpx.post(
            self.graphql_url,
            headers=self._headers(),
            json={"query": query}
        )
        response.raise_for_status()
        data = response.json()["data"]["viewer"]
        return data["login"],data["pinnedItems"]["nodes"]
        
    
    def _codesearch_headers(self):
        return{
            "Authorization": f"Token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    def get_package_json_deps(self, owner, repo):
        url = f"{self.base_url}repos/{owner}/{repo}/contents/package.json"
        response = httpx.get(url, headers=self._headers())
        response.raise_for_status()

        data = response.json()
        download_url = data["download_url"]
        content = httpx.get(download_url).json()

        deps = []
        deps.extend(content.get("dependencies", {}).keys())
        deps.extend(content.get("devDependencies", {}).keys())
        return deps
    
    def code_search(self, owner, repo, filename="package-lock.json"):
        """Search for a specific file in a repository"""
        url = f"{self.base_url}search/code?q=filename:{filename}+repo:{owner}/{repo}"
        response = httpx.get(url, headers=self._codesearch_headers())
        response.raise_for_status()
        return response.json()
        

    def get_repo_dependency_url(self,owner,repo):
        url = f"{self.base_url}repos/{owner}/{repo}/contents/requirements.txt"
        response = httpx.get(url, headers=self._headers())
        print(response)
        url=response.json()['download_url']
        ans=httpx.get(url)
        if response.status_code == 200:
            return ans.text.splitlines()
        else:
            return {"error": response.status_code, "message": response.text}
    
    def get_proj_languages(self,owner,repo):
        response=httpx.get(f"{self.base_url}repos/{owner}/{repo}/languages", headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def get_download_url(self,url):
        response=httpx.get(url)
        response_js=response.json()
        dependency_url=response_js['download_url']
        return dependency_url
    
    def dependencies_download_url(self,url):
        response=httpx.get(url)
        response_js=response.json()
        dependencies=response_js['packages']
        return dependencies
    

a = GithubClient(Github_token)
username, pinned_repos = a.get_pinned_repos()

all_repos_dependencies = {}

for repo in pinned_repos:
    repo_name = repo['name']
    repo_url = repo['url']
    url_parts = repo_url.split('/')
    owner = url_parts[-2]
    print(repo_name)
    languages = [lang['name'] for lang in repo.get('languages', {}).get('nodes', [])]
    dependencies = []
    
    # JavaScript/TypeScript dependencies
    if any(lang in ['JavaScript', 'TypeScript'] for lang in languages):
        try:
            result = a.get_package_json_deps(owner, repo_name)
            if len(result)>0:
                dependencies.extend(result)
                print(result)
            if len(result)==0:
                result=a.code_search(owner, repo_name)
                dependecy_dict = result['items'][0]
                url = dependecy_dict['url']
                download_url = a.get_download_url(url)
                packages = a.dependencies_download_url(download_url)
                backend=list(packages.get('backend').get('dependencies').keys())
                frontend=list(packages.get('frontend').get('dependencies').keys())
                if backend:
                    dependencies.extend(backend)
                if frontend:
                    dependencies.extend(frontend)
                print(backend)
                print(packages)
            
            # Extract dependencies from the root package
                if '' in packages and 'dependencies' in packages['']:
                    req_dep = packages['']['dependencies']
                    dependencies.extend(list(req_dep.keys()))
        except:
            pass
    
    # Python dependencies
    if 'Python' in languages:
        try:
            python_deps = a.get_repo_dependency_url(owner, repo_name)
            print(python_deps)
            if not isinstance(python_deps, dict):
                dependencies.extend(python_deps)
        except:
            pass
    
    all_repos_dependencies[repo_name] = {
        'languages': languages,
        'dependencies': dependencies
    }
    print(all_repos_dependencies)
    
class DependencyFilter:
    FRONTEND: Set[str] ={
    "react", "next", "vue", "angular", "svelte", "nuxt",    
    "gatsby",        # React static framework
    "remix",         # React full-stack
    "solid",         # SolidJS
    "qwik",          # Qwik
    "astro",         # Astro (multi-framework)
    # Mobile / cross-platform
    "react-native",
    "expo",
    "ionic",
    "flutter"
    }

    BACKEND: Set[str] = {
    # Node.js
    "express", "nestjs", "fastify", "koa", "hapi",

    # Python
    "django", "flask", "fastapi", "tornado", "pyramid",

    # Java / JVM
    "spring", "springboot",

    # PHP
    "laravel", "symfony",

    # Ruby
    "rails", "sinatra",

    # Go
    "gin", "echo", "fiber",

    # .NET
    "aspnet", "aspnetcore",
}

    DEVOPS: Set[str] = {
    # Containers & orchestration
    "docker", "docker-compose",
    "kubernetes", "helm",

    # IaC
    "terraform", "pulumi",

    # CI/CD
    "github-actions", "gitlab-ci", "jenkins", "circleci",

    # Cloud
    "aws", "azure", "gcp",

    # Servers / proxies
    "nginx", "apache", "traefik",
}

    DATABASE: Set[str] = {
    # SQL
    "postgresql", "mysql", "mariadb", "sqlite", "oracle", "mssql",

    # NoSQL
    "mongodb", "redis", "cassandra", "dynamodb", "couchdb",

    # Search / analytics
    "elasticsearch", "opensearch",
}


    LOW_SIGNAL_PREFIXES: tuple[str, ...] = (
    "@types/",
    "eslint",
    "prettier",
    "babel",
    "webpack",
    "rollup",
    "vite",
    "tslib",
    "core-js",
)
    LOW_SIGNAL_KEYWORDS: tuple[str, ...] = (
    "loader",
    "plugin",
    "polyfill",
    "helper",
    "helpers",
    "utils",
    "config",
    "preset",
    "adapter",
)

    @staticmethod
    def normalize_js_dep(dep: str) -> str:
        dep = dep.lower().strip()
        dep=dep.replace("_","-")
        return dep
        
    @staticmethod
    def normalize_python_dep(dep):
        dep = dep.lower().strip()
        if "==" in dep:
            dep = dep.split("==")[0]
        elif ">=" in dep:
            dep = dep.split(">=")[0]
        elif "<=" in dep:
            dep = dep.split("<=")[0]
        elif "~=" in dep:
            dep = dep.split("~=")[0]
        elif ">" in dep:
            dep = dep.split(">")[0]
        elif "<" in dep:
            dep = dep.split("<")[0]
        return dep
    
    @staticmethod
    def normalize(dep: str) -> str:
        """Generic normalization for dependencies"""
        return dep.lower().strip()

    def filter(self,languages, deps: Iterable[str]) -> Tuple[List[str], List[str]]:
        important = set()
        unknown = set()

        for dep in deps:
            if 'Python' in languages:
                name =self.normalize_python_dep(dep)
            elif any(lang in ['JavaScript', 'TypeScript'] for lang in languages):
                name =self.normalize_js_dep(dep)
            else:
                name =self.normalize(deps)
            
            if name.startswith(self.LOW_SIGNAL_PREFIXES):
                continue
            if any(k in name for k in self.LOW_SIGNAL_KEYWORDS):
                continue

            if self._is_high_signal(name):
                important.add(name)
            else:
                unknown.add(name)

        return sorted(important), sorted(unknown)

    def _is_high_signal(self, name: str) -> bool:
        return (
            name in self.FRONTEND
            or name in self.BACKEND
            or name in self.DEVOPS
            or name in self.DATABASE
        )

LLM_PROMPT_TEMPLATE = """
From the following list, return ONLY major frameworks, platforms, or tools.
Ignore utilities, helpers, build tools, and libraries.

Return JSON only.

List:
{deps}
"""

def resolve_unknown_with_llm(unknown: list[str]) -> list[str]:
    if not unknown:
        return []
    prompt = LLM_PROMPT_TEMPLATE.format(deps=unknown)
    try:
        result = structured.invoke(prompt)
        return result.dependencies
    except Exception as e:
        print("LLM error:", e)
        return []

filter_obj = DependencyFilter()
analyzed_repos = {}

# Collect all unknown dependencies first
all_unknown = set()

for repo_name, repo_data in all_repos_dependencies.items():
    deps = repo_data['dependencies']
    languages = repo_data['languages']
    important, unknown = filter_obj.filter(languages, deps)
    
    analyzed_repos[repo_name] = {
        'languages': repo_data['languages'],
        'important_deps': important,
        'unknown_deps': unknown
    }
    
    all_unknown.update(unknown[:20])

# Make ONE LLM call for all unknown dependencies
if all_unknown:
    print(f"\nResolving {len(all_unknown)} unique unknown dependencies with LLM...")
    llm_detected = resolve_unknown_with_llm(list(all_unknown))
    llm_detected_set = set(llm_detected)
else:
    llm_detected_set = set()

# Update repos with LLM results
for repo_name, repo_data in analyzed_repos.items():
    # Add any LLM-detected dependencies that were in this repo's unknown list
    additional = [dep for dep in repo_data['unknown_deps'] if dep in llm_detected_set]
    final_tech = repo_data['important_deps'] + additional
    
    print(f"\n{repo_name}:")
    print(f"  Technologies: {final_tech}")
    print(f"  Unresolved: {[d for d in repo_data['unknown_deps'] if d not in llm_detected_set]}")
