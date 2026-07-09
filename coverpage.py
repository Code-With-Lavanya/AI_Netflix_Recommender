import os
import requests
import dotenv
dotenv.load_dotenv()

API_KEY = os.getenv("OMDB_API_KEY")


def get_movie_details(title):

    try:

        response = requests.get(
            "https://www.omdbapi.com/",
            params={
                "apikey": API_KEY,
                "t": title
            },
            timeout=10
        )

        data = response.json()

        if data.get("Response") == "False":
            return None

        return data

    except Exception:

        return None