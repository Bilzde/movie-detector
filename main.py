from flask import Flask, render_template, request, redirect, jsonify
import os
import re
import requests
from werkzeug.utils import secure_filename
from google.cloud import vision
import tempfile

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['FOUNDER'] = {
    "name": "Bilal Abdi",
    "email": "bilalabdi230@gmail.com",
    "affiliate_id": "bilalabdi-20"
}

# APIs (set these in Replit secrets)
TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
GOOGLE_CREDS = json.loads(os.environ.get('GOOGLE_CREDENTIALS_JSON'))

# ===== CORE FUNCTIONALITY =====
def analyze_url(url):
    """Extract video title from URL"""
    try:
        response = requests.get(url, timeout=5)
        title = re.search(r'<title>(.+?)</title>', response.text).group(1)
        return clean_title(title)
    except:
        return None

def analyze_image(file_path):
    """Identify movie from screenshot"""
    client = vision.ImageAnnotatorClient.from_service_account_json(GOOGLE_CREDS)

    with open(file_path, 'rb') as f:
        image = vision.Image(content=f.read())

    response = client.web_detection(image=image)

    # Try multiple detection methods
    if response.web_detection.pages_with_matching_images:
        return response.web_detection.pages_with_matching_images[0].url
    elif response.web_detection.visually_similar_images:
        return response.web_detection.visually_similar_images[0].url
    else:
        labels = [label.description for label in response.label_annotations]
        return " ".join(labels[:3])

def get_movie_data(query):
    """Fetch movie info from TMDB"""
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(url).json()

    if response.get('results'):
        movie = response['results'][0]
        return {
            'title': movie['title'],
            'year': movie['release_date'][:4],
            'synopsis': movie['overview'],
            'providers': get_streaming_providers(movie['id'])
        }
    return None

# ===== ROUTES =====
@app.route('/')
def home():
    return render_template('index.html', founder=app.config['FOUNDER'])

@app.route('/detect', methods=['POST'])
def detect():
    # URL Detection
    if 'url' in request.form:
        url = request.form['url']
        if title := analyze_url(url):
            return jsonify(get_movie_data(title))

    # Screenshot Detection
    elif 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            if query := analyze_image(filepath):
                return jsonify(get_movie_data(query))

    return jsonify({"error": "Detection failed"}), 400

@app.route('/watch/<platform>/<query>')
def watch(platform, query):
    """Affiliate redirects"""
    links = {
        'prime': f"https://www.primevideo.com/search?q={query}&tag={app.config['FOUNDER']['affiliate_id']}",
        'youtube': f"https://www.youtube.com/results?search_query={query}",
        'google': f"https://www.google.com/search?q={query}+streaming"
    }
    return redirect(links.get(platform, links['google']))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)