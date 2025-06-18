import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from db import create_tables, add_user, verify_user, log_watch, get_watch_history

# ✅ Create user database tables
create_tables()

@st.cache_resource
def load_model():
    # ✅ Load your updated dataset
    df = pd.read_csv("/Users/anantlakhotiya/Documents/movie_recommender_app/cleaned_hollywood_movies_1980_2024 (1).csv")
    
    # ✅ Basic cleaning
    df = df.dropna(subset=['title', 'genre', 'language', 'directors', 'year', 'imdb_rating', 'titletype'])
    
    # ✅ Combine text fields
    df['combined'] = (
        df['title'].fillna('') + ' ' +
        df['genre'].fillna('') + ' ' +
        df['language'].fillna('') + ' ' +
        df['directors'].fillna('')
    ).str.lower()

    # ✅ TF-IDF and NearestNeighbors
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['combined'])
    nn = NearestNeighbors(n_neighbors=50, metric='cosine', algorithm='brute')
    nn.fit(tfidf_matrix)
    indices = pd.Series(df.index, index=df['title'].str.lower()).drop_duplicates()

    return df, tfidf_matrix, nn, indices

# ✅ Manage session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'email' not in st.session_state:
    st.session_state.email = ""
if 'name' not in st.session_state:
    st.session_state.name = ""

# ✅ Login / Signup screen
def show_login_signup():
    st.title("🎬 Movie Recommender Login")

    option = st.radio("Choose:", ["Login", "Signup"])
    name = st.text_input("Name", disabled=(option == "Login"))
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button(option):
        if option == "Signup":
            try:
                add_user(name, email, password)
                st.success("✅ Account created. You can now log in.")
            except:
                st.error("❌ User already exists.")
        else:
            user_name = verify_user(email, password)
            if user_name:
                st.session_state.logged_in = True
                st.session_state.email = email
                st.session_state.name = user_name
                st.rerun()
            else:
                st.error("❌ Invalid credentials.")

# ✅ Login check
if not st.session_state.logged_in:
    show_login_signup()
    st.stop()

# ✅ Main recommender logic
st.title(f"🎥 Welcome, {st.session_state.name}!")
df, tfidf_matrix, nn, indices = load_model()

titles_sorted = sorted(df['title'].dropna().unique().tolist())
selected_title = st.selectbox("Pick a movie:", titles_sorted)

apply_genre_filter = st.checkbox("Filter by similar genre", value=True)
num_recs = st.slider("Number of recommendations:", 1, 20, 5)

if st.button("Recommend"):
    title = selected_title.lower()
    if title not in indices:
        st.error("❌ Movie not found.")
    else:
        idx = indices[title]
        distances, neighbors = nn.kneighbors(tfidf_matrix[idx], n_neighbors=50)
        recommended_indices = neighbors.flatten()[1:]
        original_genres = set(df.loc[idx, 'genre'].lower().split(','))
        recommendations = []

        for i in recommended_indices:
            movie = df.iloc[i]
            movie_genres = set(str(movie['genre']).lower().split(','))
            if apply_genre_filter and not original_genres & movie_genres:
                continue
            recommendations.append(movie)
            if len(recommendations) >= num_recs:
                break

        if not recommendations:
            st.warning("No genre-matching movies found.")
        else:
            st.success("Here are your recommendations:")
            for movie in recommendations:
                log_watch(st.session_state.email, movie['title'])
                st.write(
                    f"🎞️ **{movie['title']}** ({int(movie['year'])}) — ⭐ {movie['imdb_rating']} — *{movie['titletype']}*"
                )

# ✅ Watch history
with st.expander("🕘 View Watch History"):
    history = get_watch_history(st.session_state.email)
    if not history:
        st.info("No history yet.")
    else:
        for title, time in history:
            st.write(f"• **{title}** — watched on `{time}`")

# ✅ Logout
if st.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.session_state.name = ""
    st.experimental_rerun()

