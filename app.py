from flask import Flask, render_template, request, redirect, url_for
from models import db, Article
from transformers import pipeline

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Load summarization model once at startup
print("Loading summarization model...")
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
print("Model loaded successfully.")

@app.route("/")
def index():
    articles = Article.query.all()
    return render_template("index.html", articles=articles)

@app.route("/add", methods=["POST"])
def add_article():
    title = request.form["title"]
    content = request.form["content"]

    # AI-generated summary
    summary_text = summarizer(content, max_length=50, min_length=10, do_sample=False)[0]['summary_text']

    new_article = Article(title=title, content=content, summary=summary_text)
    db.session.add(new_article)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_article(id):
    article = Article.query.get_or_404(id)
    if request.method == "POST":
        article.title = request.form["title"]
        article.content = request.form["content"]

        # Re-generate summary
        article.summary = summarizer(article.content, max_length=50, min_length=10, do_sample=False)[0]['summary_text']

        db.session.commit()
        return redirect(url_for("index"))
    return render_template("edit.html", article=article)

@app.route("/delete/<int:id>")
def delete_article(id):
    article = Article.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    # Ensure DB exists before starting the app
    with app.app_context():
        db.create_all()
    app.run(debug=True)
