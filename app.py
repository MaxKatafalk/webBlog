from flask import Flask, render_template, request, redirect, url_for
from datetime import date, datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'your-secret-key-here'

db = SQLAlchemy(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(100), unique=True, nullable=False)
	hashed_password = db.Column(db.String(100), nullable=False)
	created_date = db.Column(db.DateTime, default=datetime.utcnow)

	articles = db.relationship('Article', backref='author')

class Article(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(150), nullable=False)
	text = db.Column(db.Text, nullable=False)
	category = db.Column(db.String(50), nullable=False, default='general')
	created_date = db.Column(db.DateTime, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
	if app.debug:
		db.drop_all()
	db.create_all()
	
@app.route('/articles')
def articles():
	all_articles = Article.query.order_by(Article.created_date.desc()).all()
	
	categories = db.session.query(Article.category).distinct().all()
	categories = [x[0] for x in categories]  
	
	return render_template('articles.html', articles=all_articles, categories=categories, current_category=None)

@app.route('/articles/<category>')
def articles_by_category(category):
	category_exists = db.session.query(Article).filter_by(category=category).first()
	if not category_exists:
		return f"Категория '{category}' не найдена. <a href='/articles'>Вернуться ко всем статьям</a>", 404
	
	filtered_articles = Article.query.filter_by(category=category).order_by(Article.created_date.desc()).all()
	
	return render_template('articles.html', articles=filtered_articles, current_category=category)

@app.route('/edit-article/<int:id>', methods=['GET', 'POST'])
def edit_article(id):
	article = Article.query.get_or_404(id)
	
	if request.method == 'POST':
		article.title = request.form['title']
		article.text = request.form['content']
		article.user_id = int(request.form['user_id'])
		db.session.commit()
		return redirect(url_for('default'))
	
	users = User.query.all()
	return render_template('edit_article.html', article=article, users=users)

@app.route('/reset-db')
def reset_db():
    db.drop_all()
    db.create_all()
    return "База пересоздана!"

@app.route('/create-article', methods=['GET', 'POST'])
def create_article():
	if request.method == 'POST':
		title = request.form['title']
		content = request.form['content']
		user_id = int(request.form['user_id'])
		category = request.form.get('category', 'general')
		
		new_article = Article(
			title=title,
			text=content,
			user_id=user_id,
			category=category
		)
		
		db.session.add(new_article)
		db.session.commit()
			
		return redirect(url_for('default'))
	
	users = User.query.all()
	return render_template('create_article.html', users=users)

@app.route('/delete-article/<int:id>')
def delete_article(id):
	article = Article.query.get_or_404(id)
	db.session.delete(article)
	db.session.commit()
	
	return redirect(url_for('default'))


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
	name = ""
	email = ""
	message = ""

	if request.method == 'POST':
		name = request.form['name'].strip()
		email = request.form['email'].strip()
		message = request.form['message'].strip()
		return f"<h1> спасибо за ваше сообщение!</h1>"\
				f"<p> Имя: {name}</p>"\
				f"<p>  Email: {email}</p>"\
				f"<p>  Сообщение: {message}</p>"

	return render_template('feedback.html', name=name, email=email, message=message)
	
@app.route('/news/<int:id>')
def news(id):
	article = Article.query.get_or_404(id)
	return f"Статья {article.title}<br>Автор: {article.author.name}"

@app.route('/')
def default():
	today = date.today().isoformat()
	articles = Article.query.order_by(Article.created_date.desc()).all()
	return render_template('Web.html', articles=articles, today=today)

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/contact')
def contact():
	return render_template('contact.html')

if __name__ == "__main__":
	app.run()
