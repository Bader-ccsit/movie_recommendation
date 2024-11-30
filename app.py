from flask import Flask, request, render_template
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import requests

app = Flask(__name__)

movies = pd.read_csv('My_Movie_dataset(cleaned1)_utf8.csv')

movies['combined_features'] = (
    movies['Genre'] + ' ' +
    movies['Director'] + ' ' +
    movies['Actors'] + ' ' +
    movies['Plot']
)
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(movies['combined_features'])

#using the simularity matrix
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)


def get_recommendations(title, num_recommendations=5):
    # Convert the title to lowercase for case-insensitive matching
    title = title.lower()
    movies['lowercase_name'] = movies['Movie Name'].str.lower()

    # Check if the movie exists in the dataset
    if title not in movies['lowercase_name'].values:
        return pd.DataFrame()  # Return an empty DataFrame if not found

    # Get the index of the movie
    idx = movies[movies['lowercase_name'] == title].index[0]

    # Compute similarity scores
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:num_recommendations + 1]  # Skip the first match (itself)

    # Get the indices of similar movies
    movie_indices = [i[0] for i in sim_scores]

    # Return the recommended movies as a DataFrame
    return movies.iloc[movie_indices][['Movie Name', 'Year', 'Genre', 'imdbRating']].reset_index(drop=True)


@app.route('/')
def home():
    movie_names = movies['Movie Name'].tolist()
    return render_template('index.html', movies=movie_names)


@app.route('/recommend', methods=['POST'])
def recommend():
    movie_name = request.form.get('movie_name', '').strip()

    # Handle empty movie name submission
    if not movie_name:
        return render_template('recommendations.html', recommendations=[], movie_name="")

    # Get recommendations
    recommendations_df = get_recommendations(movie_name)

    # Ensure we convert only if it’s a DataFrame
    recommendations = (
        recommendations_df.to_dict('records') if not recommendations_df.empty else []
    )

    return render_template('recommendations.html', recommendations=recommendations, movie_name=movie_name)

@app.route('/movie/<movie_name>')
def movie_details(movie_name):
    movie = movies[movies['Movie Name'] == movie_name].iloc[0]
    poster_url = get_movie_poster(movie_name)
    return render_template('movie_details.html', movie=movie, poster_url=poster_url)




posters = pd.read_csv('posters.csv')

def get_movie_poster(movie_name):
    # Search for the movie in the posters dataset
    row = posters[posters['Movie'].str.lower() == movie_name.lower()]
    if not row.empty:
        tmdb_id = row['TMDb ID'].values[0]
        # Retrieve poster from TMDB API
        api_key = '9d7c2e7cfa61f948baee3ebfc456c82b'  # Replace with your TMDB API key
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
    return None


if __name__ == '__main__':
    app.run(debug=True)
