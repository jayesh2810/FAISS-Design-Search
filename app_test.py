import streamlit as st
import json
import os
import numpy as np
import faiss
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from cairosvg import svg2png
import io
import openai

# Load CLIP Model
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Load JSON File
with open("description_cleaned.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert SVG to PNG for embedding extraction
def convert_svg_to_png(svg_path):
    png_bytes = svg2png(url=svg_path)
    return Image.open(io.BytesIO(png_bytes))

# Load or Generate Embeddings
cache_file = "embeddings_cache.npz"
if os.path.exists(cache_file):
    cache = np.load(cache_file, allow_pickle=True)
    text_embeddings, image_embeddings = cache["text_embeddings"], cache["image_embeddings"]
    text_titles, image_titles = list(cache["text_titles"]), list(cache["image_titles"])
    image_paths = list(cache["image_paths"])
else:
    st.error("Embeddings cache not found. Please generate embeddings first.")
    st.stop()

# Merge Text & Image Embeddings for FAISS Indexing
all_embeddings = np.vstack([text_embeddings, image_embeddings])
faiss_index = faiss.IndexFlatL2(all_embeddings.shape[1])
faiss_index.add(all_embeddings)

# Create Design Info Dictionary
design_info = {entry["title"]: entry for entry in data}

# OpenAI API Setup
if "OPENAI_API_KEY" in st.secrets:
    openai_api = st.secrets["OPENAI_API_KEY"]
else:
    openai_api = st.text_input("Enter your OpenAI API Key:", type="password")
    if not openai_api:
        st.warning("Please enter your OpenAI API key to proceed.")
        st.stop()

client = openai.OpenAI(api_key=openai_api)

# Initialize Chat History in Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat Function with History
def chat_with_openai(user_query, top_k=1):
    tokenized_text = clip_processor.tokenizer(user_query, padding="max_length", truncation=True, return_tensors="pt")
    with torch.no_grad():
        query_embedding = clip_model.get_text_features(**tokenized_text).cpu().numpy().squeeze(0)

    distances, indices = faiss_index.search(query_embedding.reshape(1, -1), top_k)

    if indices[0][0] == -1:
        return "I'm sorry, but I couldn't find a relevant design for your query."

    best_match_idx = indices[0][0]
    design_title = text_titles[best_match_idx] if best_match_idx < len(text_titles) else image_titles[best_match_idx - len(text_titles)]

    if design_title not in design_info:
        return f"I found a design titled '{design_title}', but I couldn't retrieve its description."

    design_description = design_info[design_title]["content"]

    # Include chat history in the prompt
    chat_messages = [{"role": "system", "content": f"You're an expert assistant helping with engineering designs. The current topic is '{design_title}'.\n{design_description}"}]
    for message in st.session_state.chat_history:
        chat_messages.append(message)

    chat_messages.append({"role": "user", "content": user_query})

    # Generate AI Response with OpenAI
    response = client.chat.completions.create(
        model="gpt-4",
        messages=chat_messages,
        max_tokens=200
    ).choices[0].message.content

    # Store message history
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    st.session_state.chat_history.append({"role": "assistant", "content": response})

    return response

# Streamlit UI
st.title("Design Search & Chat System")

# Display chat history
st.subheader("Chat History")
for msg in st.session_state.chat_history:
    role = "User" if msg["role"] == "user" else "🤖 AI"
    st.write(f"{role}: {msg['content']}")

# User Input
query = st.text_input("Ask something about a design:")
if st.button("Send"):
    if query:
        response = chat_with_openai(query)
        st.subheader("🔹 AI Response")
        st.write(response)
    else:
        st.warning("Please enter a question.")
