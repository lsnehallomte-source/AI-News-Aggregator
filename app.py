from flask import Flask, redirect, render_template ,jsonify ,url_for ,request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import requests
from textblob import TextBlob
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///news.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

API_KEY="0d1d53713c714aed92132b3081b16999"

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300))
    category = db.Column(db.String(50))
    sentiment = db.Column(db.String(20))
    description = db.Column(db.Text)
    url = db.Column(db.String(500))
    image = db.Column(db.String(500))
    source = db.Column(db.String(100))
    published_at = db.Column(db.String(100))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300))
    image = db.Column(db.String(500))
    url = db.Column(db.String(500))
    source = db.Column(db.String(100))
    category = db.Column(db.String(50))
    sentiment = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = generate_password_hash(request.form.get("password"))

        if User.query.filter_by(email=email).first():
            return "Email already exists!"

        user = User(
            name=name,
            email=email,
            password=password
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))

    return render_template('login.html')

@app.route("/api/news")

def get_news():
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={API_KEY}"

    response = requests.get(url)
    if response.status_code != 200:
       return jsonify({"error": "Failed to fetch news"})
    data = response.json()

    articles = []

    Article.query.delete()
    db.session.commit()

    for article in data.get("articles", []):

        title = article.get("title", "").lower()

        if any(word in title for word in ["ai", "technology", "tech", "google", "microsoft", "apple"]):
             category = "Technology"
        elif any(word in title for word in ["stock", "market", "finance", "bank", "economy", "business"]):
             category = "Finance"
        elif any(word in title for word in ["cricket", "football", "sports", "match", "olympics"]):
             category = "Sports"
        else:
             category = "General"
             
        text = article.get("title", "")
        polarity = TextBlob(text).sentiment.polarity

        if polarity > 0:
             sentiment = "Positive"
        elif polarity < 0:
             sentiment = "Negative"
        else:
             sentiment = "Neutral"
        new_article = Article(
             title=article.get("title", "No Title"),
             category=category,
             sentiment=sentiment,
             description=article.get("description", "No Description"),
             url=article.get("url", "#"),
             image=article.get("urlToImage"),
             source=article.get("source", {}).get("name", "Unknown"),
             published_at=article.get("publishedAt", "")
        )

        db.session.add(new_article)

        articles.append({
            "title": article.get("title", "No Title"),
            "category": category,
            "sentiment": sentiment,
            "description": article.get("description", "No Description"),
            "url": article.get("url", "#"),
            "image": article.get("urlToImage"),
            "source": article.get("source", {}).get("name", "Unknown"),
            "publishedAt": article.get("publishedAt", "")
        
        })
    db.session.commit()
    return jsonify(articles)

@app.route("/api/stats")
def get_stats():
    total = Article.query.count()
    positive = Article.query.filter_by(sentiment="Positive").count()
    neutral = Article.query.filter_by(sentiment="Neutral").count()
    negative = Article.query.filter_by(sentiment="Negative").count()

    return jsonify({
        "total": total,
        "positive": positive,
        "neutral": neutral,
        "negative": negative
    })

@app.route("/bookmark", methods=["POST"])
@login_required
def bookmark():

    data = request.get_json()

    bookmark = Bookmark(
    title=data["title"],
    image=data["image"],
    url=data["url"],
    source=data["source"],
    category=data["category"],
    sentiment=data["sentiment"],
    user_id=current_user.id
)

    db.session.add(bookmark)
    db.session.commit()

    return jsonify({
        "message": "Bookmark saved successfully!"
    })

@app.route("/api/articles")
def get_articles():

    articles = Article.query.all()

    result = []

    for a in articles:
        result.append({
            "id": a.id,
            "title": a.title,
            "category": a.category,
            "sentiment": a.sentiment
        })

    return jsonify(result)

@app.route("/api/bookmarks")
def get_bookmarks():

    bookmarks = Bookmark.query.all()

    result = []

    for b in bookmarks:
        result.append({
            "id": b.id,
            "title": b.title
        })

    return jsonify(result)

@app.route("/bookmarks")
@login_required
def bookmarks():

    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "bookmarks.html",
        bookmarks=bookmarks
    )

if __name__ == "__main__":
    app.run(debug=True)
