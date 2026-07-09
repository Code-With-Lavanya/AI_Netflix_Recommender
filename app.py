import re
import html as html_lib

import streamlit as st

from main import get_recommendation
from coverpage import get_movie_details

# --------------------------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Netflix | Your Next Favorite",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------
# STYLES
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Roboto:wght@300;400;500;700;900&display=swap');

    :root{
        --netflix-black:#141414;
        --netflix-black-2:#181818;
        --netflix-red:#E50914;
        --netflix-red-dark:#B20710;
        --netflix-text:#E5E5E5;
        --netflix-grey:#808080;
    }

    #MainMenu, header, footer {visibility: hidden;}

    .stApp{
        background: radial-gradient(ellipse at top, #1a0000 0%, #141414 55%, #000000 100%);
        color: var(--netflix-text);
        font-family: 'Roboto', sans-serif;
    }

    .block-container{
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1300px;
    }

    /* ---------------- NAVBAR / HERO ---------------- */
    .navbar{ display:flex; align-items:center; gap: 10px; margin-bottom: 8px; }
    .netflix-logo{
        font-family:'Bebas Neue', sans-serif;
        font-size: 3rem;
        letter-spacing: 2px;
        color: var(--netflix-red);
        text-shadow: 0 0 18px rgba(229,9,20,0.55);
        margin: 0;
    }
    .netflix-logo span{ color:#ffffff; }

    .hero-tagline{
        font-size: 1.15rem;
        color: var(--netflix-text);
        font-weight: 300;
        margin: 6px 0 28px 0;
        border-left: 3px solid var(--netflix-red);
        padding-left: 12px;
        animation: fadeIn 1s ease-in;
    }

    @keyframes fadeIn{ from{opacity:0; transform: translateY(-6px);} to{opacity:1; transform: translateY(0);} }

    /* ---------------- SEARCH INPUT ---------------- */
    .stTextInput > div > div > input{
        background-color: #1f1f1f;
        color: #ffffff;
        border: 1px solid #3a3a3a;
        border-radius: 4px;
        padding: 12px 14px;
        font-size: 1rem;
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
    }
    .stTextInput > div > div > input:focus{
        border-color: var(--netflix-red);
        box-shadow: 0 0 0 1px var(--netflix-red);
    }
    .stTextInput label{ color: var(--netflix-grey) !important; }

    .stButton > button{
        background-color: var(--netflix-red);
        color: #ffffff;
        border: none;
        border-radius: 4px;
        padding: 0.6rem 1.6rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: transform 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
    }
    .stButton > button:hover{
        background-color: var(--netflix-red-dark);
        transform: scale(1.04);
        box-shadow: 0 6px 18px rgba(229,9,20,0.45);
    }

    /* ---------------- INTRO / OUTRO TEXT ---------------- */
    .intro-text{ font-size: 1.05rem; color: #ffffff; margin: 4px 0 6px 0; animation: fadeIn 0.6s ease; }
    .outro-text{
        font-size: 0.92rem;
        color: var(--netflix-grey);
        margin-top: 26px;
        padding-top: 14px;
        border-top: 1px solid #2a2a2a;
        animation: fadeIn 0.6s ease;
    }

    /* ---------------- MOVIE CARD ROW ---------------- */
    .row-title{ font-size: 1.4rem; font-weight: 700; color: #ffffff; margin: 22px 0 14px 0; }

    .card-row{
        display:flex;
        gap: 18px;
        overflow-x: auto;
        overflow-y: visible;
        padding: 28px 4px 26px 4px;
        scrollbar-width: thin;
        scrollbar-color: var(--netflix-red) #1a1a1a;
    }
    .card-row::-webkit-scrollbar{ height: 8px; }
    .card-row::-webkit-scrollbar-track{ background:#1a1a1a; border-radius:10px;}
    .card-row::-webkit-scrollbar-thumb{ background: var(--netflix-red); border-radius:10px;}

    .movie-card{
        position: relative;
        flex: 0 0 200px;
        height: 300px;
        border-radius: 6px;
        overflow: hidden;
        background:#1f1f1f;
        cursor: pointer;
        box-shadow: 0 4px 14px rgba(0,0,0,0.6);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        animation: cardIn 0.5s ease backwards;
    }
    @keyframes cardIn{ from{ opacity:0; transform: translateY(18px);} to{ opacity:1; transform: translateY(0);} }

    .movie-card:hover{
        transform: scale(1.1) translateY(-10px);
        box-shadow: 0 20px 36px rgba(0,0,0,0.8);
        z-index: 6;
    }
    .movie-card img{ width: 100%; height: 100%; object-fit: cover; display:block; transition: filter 0.3s ease; }
    .movie-card:hover img{ filter: brightness(0.35); }

    .rating-badge{
        position:absolute; top:8px; right:8px;
        background: rgba(0,0,0,0.75);
        color:#f5c518;
        font-size: 0.72rem;
        font-weight:700;
        padding: 3px 7px;
        border-radius: 4px;
        border: 1px solid #f5c518;
        z-index: 2;
    }

    /* Always-visible bottom title strip */
    .base-label{
        position:absolute; left:0; right:0; bottom:0;
        padding: 8px 10px 9px;
        background: linear-gradient(to top, rgba(0,0,0,0.92), rgba(0,0,0,0));
        transition: opacity 0.25s ease;
    }
    .movie-card:hover .base-label{ opacity: 0; }
    .card-title{
        color:#fff; font-weight:700; font-size: 0.85rem;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }

    /* Hover-only detail overlay: genre / director / story / why */
    .hover-overlay{
        position:absolute; inset:0;
        background: linear-gradient(180deg, rgba(20,20,20,0.88), rgba(8,8,8,0.97) 45%);
        padding: 12px 12px 10px;
        opacity: 0;
        pointer-events: none;
        overflow-y: auto;
        transition: opacity 0.3s ease;
        font-size: 0.72rem;
        line-height: 1.4;
    }
    .movie-card:hover .hover-overlay{ opacity: 1; pointer-events: auto; }
    .hover-overlay::-webkit-scrollbar{ width: 4px; }
    .hover-overlay::-webkit-scrollbar-thumb{ background: var(--netflix-red); border-radius: 4px; }

    .hov-title{ color:#fff; font-weight:700; font-size: 0.95rem; margin-bottom: 6px; line-height:1.25; }
    .hov-row{ display:flex; justify-content:space-between; color:#f5c518; font-weight:600; margin-bottom:6px; }
    .hov-line{ color: var(--netflix-text); margin-bottom: 5px; }
    .hov-line b{ color:#fff; }
    .hov-desc{
        color:#c7c7c7; margin-bottom:6px;
        display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;
    }
    .hov-why{
        color:#ff9a9e; font-style: italic;
        display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
    }

    .empty-hint{ color: var(--netflix-grey); font-style: italic; margin-top: 20px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="navbar">
        <div class="netflix-logo">AI <span>NETFLIX</span></div>
    </div>
    <div class="hero-tagline">Tell me your mood, a genre, an actor, or a vibe — I'll find your next favorite.</div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# SEARCH
# --------------------------------------------------------------------------
if "answer" not in st.session_state:
    st.session_state.answer = None
if "query" not in st.session_state:
    st.session_state.query = ""

col1, col2 = st.columns([5, 1])
with col1:
    query = st.text_input(
        "Search",
        placeholder="e.g. a dark thriller like Se7en, or a feel-good movie with Tom Hanks",
        label_visibility="collapsed",
    )
with col2:
    search_clicked = st.button("Search", use_container_width=True)

if search_clicked and query.strip():
    with st.spinner("Scanning the catalog for your next favorite..."):
        st.session_state.answer = get_recommendation(query)
        st.session_state.query = query

# --------------------------------------------------------------------------
# PARSING THE AI ANSWER INTO STRUCTURED MOVIES
# --------------------------------------------------------------------------
# The prompt's output format re-uses the same 🎬 emoji for both "Title" and
# "Director", so we can't key off emoji alone. Instead we walk the fields in
# the exact order the prompt asks for and track position, which also lets us
# split multiple recommendations out of one continuous answer.
FIELD_SEQUENCE = [
    ("title", "🎬"),
    ("rating", "⭐"),
    ("genre", "🎭"),
    ("year", "📅"),
    ("director", "🎬"),
    ("story", "📝"),
    ("why", "💡"),
]

LABEL_STRIP = {
    "rating": r"^(IMDb\s*)?Rating:?\s*",
    "genre": r"^Genres?:?\s*",
    "year": r"^Release\s*Year:?\s*",
    "director": r"^Director:?\s*",
    "story": r"^Short\s*Story:?\s*",
    "why": r"^Why\s*this\s*is\s*recommended:?\s*",
}


def clean_value(field_name, value):
    value = value.strip()
    if field_name in LABEL_STRIP:
        value = re.sub(LABEL_STRIP[field_name], "", value, flags=re.IGNORECASE)
    return value.strip().strip("*").strip()


def parse_recommendations(answer_text):
    n = len(FIELD_SEQUENCE)
    pointer = 0
    current = {}
    movies = []
    intro_lines = []
    outro_lines = []
    started = False

    for line in answer_text.split("\n"):
        stripped = line.strip()
        expected_name, expected_emoji = FIELD_SEQUENCE[pointer]

        if stripped.startswith(expected_emoji):
            value = clean_value(expected_name, stripped[len(expected_emoji):])
            current[expected_name] = value
            started = True
            pointer += 1
            if pointer == n:
                movies.append(current)
                current = {}
                pointer = 0
        elif not started:
            intro_lines.append(line)
        elif pointer == 0:
            outro_lines.append(line)
        else:
            field_name = FIELD_SEQUENCE[pointer - 1][0]
            if stripped:
                current[field_name] = clean_value(field_name, current.get(field_name, "") + " " + stripped)

    if current.get("title"):
        movies.append(current)

    intro = "\n".join(intro_lines).strip()

    outro = "\n".join(
        l for l in outro_lines if l.strip() and not re.fullmatch(r"-{3,}", l.strip())
    ).strip()

    if not movies and not intro:
        intro = answer_text.strip()

    return intro, movies, outro


PLACEHOLDER_POSTER = "https://via.placeholder.com/300x445/1f1f1f/E50914?text=No+Poster"


def render_card(movie):
    title = movie.get("title", "")
    details = get_movie_details(title) if title else None

    if details and details.get("Poster") and details.get("Poster") != "N/A":
        poster = details["Poster"]
    else:
        poster = PLACEHOLDER_POSTER

    safe_title = html_lib.escape(title)
    rating = html_lib.escape(movie.get("rating") or "—")
    genre = html_lib.escape(movie.get("genre") or "—")
    year = html_lib.escape(movie.get("year") or "—")
    director = html_lib.escape(movie.get("director") or "—")
    story = html_lib.escape(movie.get("story") or "")
    why = html_lib.escape(movie.get("why") or "")

    parts = [
        '<div class="movie-card">',
        f'<img src="{poster}" alt="{safe_title}">',
        f'<div class="rating-badge">⭐ {rating}</div>',
        '<div class="base-label">',
        f'<div class="card-title">{safe_title}</div>',
        '</div>',
        '<div class="hover-overlay">',
        f'<div class="hov-title">{safe_title}</div>',
        f'<div class="hov-row"><span>⭐ {rating}</span><span>📅 {year}</span></div>',
        f'<div class="hov-line"><b>Genre:</b> {genre}</div>',
        f'<div class="hov-line"><b>Director:</b> {director}</div>',
    ]
    if story:
        parts.append(f'<div class="hov-desc">{story}</div>')
    if why:
        parts.append(f'<div class="hov-why">💡 {why}</div>')
    parts.append('</div>')
    parts.append('</div>')

    return "".join(parts)


def render_row(movies):
    return '<div class="card-row">' + "".join(render_card(m) for m in movies) + '</div>'


# --------------------------------------------------------------------------
# RESULTS
# --------------------------------------------------------------------------
if st.session_state.answer:
    intro, movies, outro = parse_recommendations(st.session_state.answer)

    if intro:
        st.markdown(f'<div class="intro-text">{html_lib.escape(intro)}</div>', unsafe_allow_html=True)

    if movies:
        st.markdown(
            f'<div class="row-title">Recommended for &quot;{html_lib.escape(st.session_state.query)}&quot;</div>',
            unsafe_allow_html=True,
        )
        st.markdown(render_row(movies), unsafe_allow_html=True)

    if outro:
        st.markdown(f'<div class="outro-text">{html_lib.escape(outro)}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="empty-hint">Start typing above to get personalized recommendations.</div>', unsafe_allow_html=True)