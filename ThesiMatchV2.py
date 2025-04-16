

import os
import streamlit as st
import anthropic
from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict

#Claude key
os.environ["ANTHROPIC_API_KEY"] = "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"
client = anthropic.Anthropic()

# Define the graph's state structure
class State(TypedDict, total=False):
    name: str
    description: str
    tags: List[str]
    recommendations: List[Dict]

# Define trending student interests
trending_student_interests = [
    "AI", "Sustainability", "Healthcare", "Data Science", "Robotics", "Supply Chain"
]

# Function to calculate topic relevance
def compute_relevance(tags: List[str]) -> int:
    matches = [tag for tag in tags if tag in trending_student_interests]
    return round((len(matches) / len(tags)) * 100) if tags else 0

def claude_topic_generator(state: State) -> State:
    prompt = (
        f"Suggest 2 innovative thesis project titles for a company called '{state['name']}'.\n"
        f"Project description: {state['description']}\n"
        f"Key focus areas: {', '.join(state['tags'])}\n"
        f"Format:\n1. Title one\n2. Title two"
    )

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=100,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.content[0].text.strip()
    ideas = [line.strip("•1234567890. ") for line in content.split("\n") if line.strip()]

    state["recommendations"] = [
        {"title": idea, "relevance": compute_relevance(state["tags"])} for idea in ideas
    ]
    return state

# Build and compile LangGraph
graph = StateGraph(State)
graph.add_node("claude_topic_generator", claude_topic_generator)
graph.add_node("end", lambda state: state)
graph.set_entry_point("claude_topic_generator")
graph.add_edge("claude_topic_generator", "end")

company_graph = graph.compile()

streamlit_code = '''
import streamlit as st
from __main__ import company_graph

st.set_page_config(page_title="ThesiMatch – Company Topic Generator")
st.title("🧠 ThesiMatch – AI-Powered Thesis Topics for Companies")

with st.form("company_input"):
    name = st.text_input("Company name", "MedTech AG")
    description = st.text_area(
        "Describe your thesis project opportunity",
        "Applying AI to optimize hospital resources."
    )
    tags_input = st.text_input("Key areas (comma separated)", "AI, Operations, Healthcare")
    submitted = st.form_submit_button("Generate Thesis Topics")

if submitted:
    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
    state = {
        "name": name,
        "description": description,
        "tags": tags
    }
    with st.spinner("Talking to Claude..."):
        output = company_graph.invoke(state)

    st.subheader("✨ Suggested Thesis Topics")
    for topic in output.get("recommendations", []):
        st.markdown(f"**• {topic['title']}**")
        st.caption(f"📊 Relevance Score: {topic['relevance']}% match with student interests")
'''
with open("thesimatch_app.py", "w", encoding="utf-8") as f:
    f.write(streamlit_code)

