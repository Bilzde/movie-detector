from flask import Flask, request, render_template, redirect, url_for
import requests
import os

app = Flask(__name__)

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(url)
    data = response.json()
    results = data.get("results", [])
    return render_template("index.html", movies=results, searched=query)

if __name__ == '__main__':
    app.run(debug=True)
