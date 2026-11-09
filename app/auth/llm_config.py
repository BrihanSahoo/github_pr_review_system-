from auth.config import settings
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)



# ----------------- CHAT MODEL ---------------------
llm = ChatGoogleGenerativeAI(
    model = settings.GEMINI_MODEL,
    temperature = 0,
    google_api_key = settings.GEMINI_API_KEY
)

# ------------------ EMBEDDING MODEL ----------------

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2-preview",
    google_api_key = settings.GEMINI_API_KEY
)