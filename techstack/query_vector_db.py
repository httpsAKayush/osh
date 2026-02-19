from fetch_project_data import vector_presist
res=vector_presist.similarity_search_with_score(
    query="['Next.js', 'React', 'Tailwind CSS', 'Material UI']",
    k=2
)
print(res)
