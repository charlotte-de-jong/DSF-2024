{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "974882d2-9695-4724-b2cf-f703dfd309c0",
   "metadata": {},
   "outputs": [],
   "source": [
    "!pip install langgraph streamlit anthropic --quiet"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "id": "8165f07c-7a8c-49b4-b84b-1008f8b61799",
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "import streamlit as st\n",
    "import anthropic\n",
    "from langgraph.graph import StateGraph\n",
    "from typing import TypedDict, List, Dict"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "id": "c4aef250-fe38-4b4e-b8a3-c2b752ad189e",
   "metadata": {},
   "outputs": [],
   "source": [
    "#Claude key\n",
    "os.environ[\"ANTHROPIC_API_KEY\"] = \"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\"\n",
    "client = anthropic.Anthropic()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "id": "d7a8373f-fd7a-4571-a6dd-b19ec27276ae",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Define the graph's state structure\n",
    "class State(TypedDict, total=False):\n",
    "    name: str\n",
    "    description: str\n",
    "    tags: List[str]\n",
    "    recommendations: List[Dict]\n",
    "\n",
    "# Define trending student interests\n",
    "trending_student_interests = [\n",
    "    \"AI\", \"Sustainability\", \"Healthcare\", \"Data Science\", \"Robotics\", \"Supply Chain\"\n",
    "]\n",
    "\n",
    "# Function to calculate topic relevance\n",
    "def compute_relevance(tags: List[str]) -> int:\n",
    "    matches = [tag for tag in tags if tag in trending_student_interests]\n",
    "    return round((len(matches) / len(tags)) * 100) if tags else 0"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "id": "a61d6c58-dac8-45ae-9e81-f6768e73e151",
   "metadata": {},
   "outputs": [],
   "source": [
    "\n",
    "def claude_topic_generator(state: State) -> State:\n",
    "    prompt = (\n",
    "        f\"Suggest 2 innovative thesis project titles for a company called '{state['name']}'.\\n\"\n",
    "        f\"Project description: {state['description']}\\n\"\n",
    "        f\"Key focus areas: {', '.join(state['tags'])}\\n\"\n",
    "        f\"Format:\\n1. Title one\\n2. Title two\"\n",
    "    )\n",
    "\n",
    "    response = client.messages.create(\n",
    "        model=\"claude-3-sonnet-20240229\",\n",
    "        max_tokens=100,\n",
    "        temperature=0.7,\n",
    "        messages=[{\"role\": \"user\", \"content\": prompt}]\n",
    "    )\n",
    "\n",
    "    content = response.content[0].text.strip()\n",
    "    ideas = [line.strip(\"•1234567890. \") for line in content.split(\"\\n\") if line.strip()]\n",
    "\n",
    "    state[\"recommendations\"] = [\n",
    "        {\"title\": idea, \"relevance\": compute_relevance(state[\"tags\"])} for idea in ideas\n",
    "    ]\n",
    "    return state\n",
    "\n",
    "# Build and compile LangGraph\n",
    "graph = StateGraph(State)\n",
    "graph.add_node(\"claude_topic_generator\", claude_topic_generator)\n",
    "graph.add_node(\"end\", lambda state: state)\n",
    "graph.set_entry_point(\"claude_topic_generator\")\n",
    "graph.add_edge(\"claude_topic_generator\", \"end\")\n",
    "\n",
    "company_graph = graph.compile()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "id": "145b0c54-4fe8-4df1-ba7d-e55e5d7d859a",
   "metadata": {},
   "outputs": [],
   "source": [
    "streamlit_code = '''\n",
    "import streamlit as st\n",
    "from __main__ import company_graph\n",
    "\n",
    "st.set_page_config(page_title=\"ThesiMatch – Company Topic Generator\")\n",
    "st.title(\"🧠 ThesiMatch – AI-Powered Thesis Topics for Companies\")\n",
    "\n",
    "with st.form(\"company_input\"):\n",
    "    name = st.text_input(\"Company name\", \"MedTech AG\")\n",
    "    description = st.text_area(\n",
    "        \"Describe your thesis project opportunity\",\n",
    "        \"Applying AI to optimize hospital resources.\"\n",
    "    )\n",
    "    tags_input = st.text_input(\"Key areas (comma separated)\", \"AI, Operations, Healthcare\")\n",
    "    submitted = st.form_submit_button(\"Generate Thesis Topics\")\n",
    "\n",
    "if submitted:\n",
    "    tags = [tag.strip() for tag in tags_input.split(\",\") if tag.strip()]\n",
    "    state = {\n",
    "        \"name\": name,\n",
    "        \"description\": description,\n",
    "        \"tags\": tags\n",
    "    }\n",
    "    with st.spinner(\"Talking to Claude...\"):\n",
    "        output = company_graph.invoke(state)\n",
    "\n",
    "    st.subheader(\"✨ Suggested Thesis Topics\")\n",
    "    for topic in output.get(\"recommendations\", []):\n",
    "        st.markdown(f\"**• {topic['title']}**\")\n",
    "        st.caption(f\"📊 Relevance Score: {topic['relevance']}% match with student interests\")\n",
    "'''\n",
    "\n",
    "with open(\"thesimatch_app.py\", \"w\", encoding=\"utf-8\") as f:\n",
    "    f.write(streamlit_code)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "032f0ade-87ac-45a1-8932-f07cc9d8376c",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.13.2"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
