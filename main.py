import pandas as pd
import json
import os
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

df = pd.read_csv("C:\\Users\\Lucky\\Downloads\\archive\\netflix_movies_detailed_up_to_2025.csv")

df = df.dropna(subset=["description"])
df = df.drop_duplicates(subset=["title"])
df.drop(columns=["show_id", "date_added", "popularity", "vote_count", "budget", "revenue", "duration"], inplace=True)

movie_documents = []

for _, row in df.iterrows():

    text = f"""
    Title: {row['title']}

    Type: {row['type']}

    Genres: {row['genres']}

    Release Year: {row['release_year']}

    Director: {row['director']}

    Cast: {row['cast']}

    Country: {row['country']}

    Language: {row['language']}

    IMDb Rating: {row['vote_average']}

    Description:
    {row['description']}
    """

    movie_documents.append(
        Document(
            page_content=text,
            metadata={
                "title": row["title"],
                "genre": row["genres"],
                "year": row["release_year"],
                "language": row["language"],
                "type": row["type"]
            }
        )
    )


embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

llm = ChatMistralAI(
    model="mistral-small-latest",
    api_key=os.getenv("MISTRAL_API_KEY")
)


DB_PATH = "vector_db"

if os.path.exists(DB_PATH):
    print("Loading existing Vector DB...")

    vector_db = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embedding_model
    )

else:
    print("Creating Vector DB for first time...")

    vector_db = Chroma.from_documents(
        documents=movie_documents,
        embedding=embedding_model,
        persist_directory=DB_PATH
    )

retriever = vector_db.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5,
        "fetch_k": 20
    }
)
ANALYZER_PROMPT = ANALYZER_PROMPT = ANALYZER_PROMPT = """
You are a query analyzer.

Extract movie search filters from the user query.

Return ONLY valid JSON.

Do NOT explain.
Do NOT write markdown.
Do NOT wrap the JSON inside ```json.

Return exactly this schema:

{
  "genre": [],
  "actors": [],
  "directors": [],
  "language": "",
  "country": "",
  "year": null,
  "year_range": null,
  "movie_type": "",
  "mood": "",
  "keywords": [],
  "query": ""
}

Examples

User:
Suggest action movies of Sunny Deol after 2000

Output:
{
  "genre":["Action"],
  "actors":["Sunny Deol"],
  "directors":[],
  "language":"",
  "country":"",
  "year":2000,
  "year_range":null,
  "movie_type":"movie",
  "mood":"",
  "keywords":["action","Sunny Deol"],
  "query":"Suggest action movies of Sunny Deol after 2000"
}
Return year_range as integers, not strings.
Return ONLY JSON.
"""

SYSTEM_PROMPT = """
You are AI Entertainment Copilot, an expert movie and TV recommendation assistant.

Your goal is to help users discover the best entertainment based on their interests, mood, preferences, favorite actors, directors, genres, release years, and viewing context.

========================
RULES
========================

1. Use ONLY the retrieved movie information provided in the context.

2. Never invent
- movie titles
- ratings
- actors
- directors
- release years
- genres
- descriptions

3. If the retrieved context doesn't contain enough information,
say:

"I couldn't find enough relevant information in my knowledge base."

Do NOT hallucinate.

4. Explain WHY every recommendation matches the user's request.

5. Rank recommendations from best to least relevant.

6. Keep recommendations personalized.

7. If the user mentions:

- mood
- actor
- director
- genre
- language
- release year
- country

prioritize those attributes.

8. Never mention

- embeddings
- vector database
- LangChain
- retrieval
- RAG
- AI implementation

9. Be conversational.

========================
OUTPUT FORMAT
========================

Start with a friendly introduction.

For each recommendation:

🎬 Title

⭐ IMDb Rating

🎭 Genre

📅 Release Year

🎬 Director

📝 Short Story

💡 Why this is recommended

--------------------------------

End with

"Enjoy your movie! 🍿"

Then ask ONE follow-up question that keeps the conversation going.

Example:

"Would you like something darker, funnier, or more emotional?"
"""
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        SYSTEM_PROMPT
    ),
    (
        "human",
        """
Retrieved Context:

{context}

User Question:

{query}
"""
    )
])
chain = prompt | llm


def get_recommendation(query):
    """Runs the retrieval + LLM chain for a single user query and returns the answer text."""

    response = llm.invoke(ANALYZER_PROMPT + query)

    print("========== RAW RESPONSE ==========")
    print(response.content)
    print("==================================")

    filters = json.loads(response.content)
    content = response.content.strip()

    if content.startswith("```json"):
        content = content.replace("```json","").replace("```","").strip()

    filtered_df = df.copy()

    print("Original:", len(filtered_df))

    if filters.get("genre"):

        genre = filters["genre"][0].lower()

        filtered_df = filtered_df[
            filtered_df["genres"]
            .str.lower()
            .str.contains(genre, na=False)
        ]

        print("After Genre:", len(filtered_df))

    if filters.get("year_range"):

        start, end = filters["year_range"]

        filtered_df = filtered_df[
            filtered_df["release_year"].between(start, end)
        ]

        print("After Year:", len(filtered_df))
    filtered_documents = []
    print(df["release_year"].dtype)

    for _, row in filtered_df.iterrows():

        filtered_documents.append(
            Document(
                page_content=f"""
                Title: {row['title']}
                Genres: {row['genres']}
                Cast: {row['cast']}
                Description:
                {row['description']}
                """
                        )
                    )
    print("Filtered Movies:", len(filtered_df))
    print("Filtered Documents:", len(filtered_documents))

    print(df["release_year"].dtype)

    print(df[df["genres"].str.contains("Comedy", case=False, na=False)].shape)

    print(df[df["release_year"].between(2000,2009)].shape)

    print(df[
        (df["genres"].str.contains("Comedy", case=False, na=False))
        &
        (df["release_year"].between(2000,2009))
        ].shape)
    
    print(type(embedding_model))

    print(filtered_documents[0])

    print(len(embedding_model.embed_query("hello")))

    print(type(embedding_model.embed_query("hello")))

    filtered_db = Chroma.from_documents(
    documents=filtered_documents,
    embedding=embedding_model
    )

    retriever = filtered_db.as_retriever(
    search_kwargs={
        "k":5
    })
    
    docs = retriever.invoke(query)
    context = "\n\n".join(
    doc.page_content
    for doc in docs
    )
    response = chain.invoke({
    "context": context,
    "query": query
    })
    return response.content

if __name__ == "__main__":
    query = input("You: ")
    print(get_recommendation(query))