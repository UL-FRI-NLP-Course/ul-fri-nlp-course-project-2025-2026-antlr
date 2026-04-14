from datetime import datetime

from database.vector_store import VectorStore
from services.synthesizer import Synthesizer
from timescale_vector import client

# Initialize VectorStore
vec = VectorStore()

# --------------------------------------------------------------
# Relevant question
# --------------------------------------------------------------

relevant_question = "Kolikokrat lahko ponavljam izpit, če sem padel 1. rok?"
results = vec.search(relevant_question, limit=3)
print(f"Search results for relevant question: {len(results)}")
for idx, row in results.iterrows():
    created_at = row.get("created_at", "N/A")
    score = row["distance"]
    content = row["content"][:100]  # First 100 characters

    print(f"{idx + 1}. (Score: {score:.4f}) - Created: {created_at}")
    print(f"   Content: {content}...")
    print("-" * 20)

print("===============")
response = Synthesizer.generate_response(question=relevant_question, context=results)[0]['generated_text']
print("Vprašanje: %s"%response[-2]['content'])
print("Odgovor: %s"%response[-1]['content'])
print("===============")
# TODO: response with thought process?
# print(f"\n{response.answer}")
# print("\nThought process:")
# for thought in response.thought_process:
#     print(f"- {thought}")
# print(f"\nContext: {response.enough_context}")

# --------------------------------------------------------------
# Irrelevant question
# --------------------------------------------------------------

irrelevant_question = "Kakšno je vreme v Ljubljani?"

results = vec.search(irrelevant_question, limit=3)

# response = Synthesizer.generate_response(question=irrelevant_question, context=results)
print("===============")
response = Synthesizer.generate_response(question=irrelevant_question, context=results)[0]['generated_text']
print("Vprašanje: %s"%response[-2]['content'])
print("Odgovor: %s"%response[-1]['content'])
print("===============")

# TODO: response with thought process?
# print(f"\n{response.answer}")
# print("\nThought process:")
# for thought in response.thought_process:
#     print(f"- {thought}")
# print(f"\nContext: {response.enough_context}")

# --------------------------------------------------------------
# Metadata filtering
# --------------------------------------------------------------

# metadata_filter = {"category": "Shipping"}

# results = vec.search(relevant_question, limit=3, metadata_filter=metadata_filter)

# response = Synthesizer.generate_response(question=relevant_question, context=results)

# print(f"\n{response.answer}")
# print("\nThought process:")
# for thought in response.thought_process:
#     print(f"- {thought}")
# print(f"\nContext: {response.enough_context}")

# --------------------------------------------------------------
# Advanced filtering using Predicates
# --------------------------------------------------------------

# predicates = client.Predicates("category", "==", "Shipping")
# results = vec.search(relevant_question, limit=3, predicates=predicates)


# predicates = client.Predicates("category", "==", "Shipping") | client.Predicates(
#     "category", "==", "Services"
# )
# results = vec.search(relevant_question, limit=3, predicates=predicates)


# predicates = client.Predicates("category", "==", "Shipping") & client.Predicates(
#     "created_at", ">", "2024-09-01"
# )
# results = vec.search(relevant_question, limit=3, predicates=predicates)

# --------------------------------------------------------------
# Time-based filtering
# --------------------------------------------------------------

# September — Returning results
time_range = (datetime(2024, 9, 1), datetime(2024, 9, 30))
results = vec.search(relevant_question, limit=3, time_range=time_range)

# August — Not returning any results
time_range = (datetime(2024, 8, 1), datetime(2024, 8, 30))
results = vec.search(relevant_question, limit=3, time_range=time_range)
