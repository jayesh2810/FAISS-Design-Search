# FAISS-Design-Search
An AI-powered chatbot that enables **design search and interaction** using **FAISS and CLIP embeddings**. It retrieves design descriptions **scraped from the Renesas website** and allows users to query and chat about them via OpenAI's GPT.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git
   cd YOUR_REPO_NAME
2. Install Dependencies:
   ```bash
   pip install streamlit python-dotenv
3. Create a .env file in the project directory and add the following line:
   ```bash
   OPENAI_API_KEY=your_api_key_here
4. Navigate to the project directory and run the script using following command:
   ```bash
   streamlit run app.py
