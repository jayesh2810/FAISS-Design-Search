# FAISS-Design-Search

An AI-powered chatbot that enables **design search and interaction** using **FAISS and CLIP embeddings**. It retrieves design descriptions **scraped from the Renesas website** and allows users to query and chat about them via OpenAI's GPT.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jayesh2810/FAISS-Design-Search.git
   cd FAISS-Design-Search
   ```
2. Install Dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Scrape the design data from Renesas website
   ```bash
   python scraper.py
   ```
4. Generate Embeddings (Automatically on First Run):
   When you run the main script (app.py), it automatically generates embeddings from the scraped data and stores them in embeddings_cache.npz to speed up future searches.
   If embeddings_cache.npz already exists, it will be loaded instead of regenerating embeddings.
5. Create a .env file in the project directory and add the following line:
   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```
6. Navigate to the project directory and run the script using following command:
   ```bash
   streamlit run app.py
   ```
