from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import date, datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'secret-key'

db = SQLAlchemy(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(100), unique=True, nullable=False)
	hashed_password = db.Column(db.String(100), nullable=False)
	created_date = db.Column(db.DateTime, default=datetime.utcnow)
	articles = db.relationship('Article', backref='author')
	def set_password(self, password):
		self.hashed_password = generate_password_hash(password)
	
	def check_password(self, password):
		return check_password_hash(self.hashed_password, password)

class Article(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(150), nullable=False)
	text = db.Column(db.Text, nullable=False)
	category = db.Column(db.String(50), nullable=False, default='general')
	created_date = db.Column(db.DateTime, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	
class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	text = db.Column(db.Text, nullable=False)
	date = db.Column(db.DateTime, default=datetime.utcnow)
	article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
	author_name = db.Column(db.String(100), nullable=False)
	
	article = db.relationship('Article', backref=db.backref('comments'))

with app.app_context():
	if app.debug:
		db.drop_all()
	db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		name = request.form['name']
		email = request.form['email']
		password = request.form['password']

		existing_user = User.query.filter_by(email=email).first()
		if existing_user:
				flash('Пользователь с таким email уже существует', 'error')
				return render_template('register.html')
		
		new_user = User(
				name=name,
				email=email,
				hashed_password=generate_password_hash(password)
		)
		
		db.session.add(new_user)
		db.session.commit()
		
		flash('Регистрация успешна! Теперь вы можете войти.', 'success')
		return redirect(url_for('login'))
	
	return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		
		user = User.query.filter_by(email=email).first()
		
		if user and check_password_hash(user.hashed_password, password):
				session['user_id'] = user.id
				session['user_name'] = user.name
				flash(f'Добро пожаловать, {user.name}!', 'success')
				return redirect(url_for('default'))
		else:
				flash('Неверный email или пароль', 'error')
	
	return render_template('login.html')

@app.route('/logout')
def logout():
	session.clear()
	flash('Вы вышли из системы', 'info')
	return redirect(url_for('default'))

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
	if 'user_id' not in session:
		flash('Войдите в систему для редактирования статей', 'error')
		return redirect(url_for('login'))
	
	article = Article.query.get_or_404(id)
	
	if article.user_id != session['user_id']:
		flash('Вы можете редактировать только свои статьи', 'error')
		return redirect(url_for('default'))
	
	if request.method == 'POST':
		article.title = request.form['title']
		article.text = request.form['content']
		article.category = request.form['category']
		
		db.session.commit()
		flash('Статья успешно обновлена!', 'success')
		return redirect(url_for('default'))
	
	return render_template('edit_article.html', article=article)

@app.route('/reset-db')
def reset_db():
    db.drop_all()
    db.create_all()
    return "База пересоздана!"

@app.route('/create-article', methods=['GET', 'POST'])
def create_article():
	if 'user_id' not in session:
			flash('Пожалуйста, войдите в систему для создания статей', 'error')
			return redirect(url_for('login'))
	
	if request.method == 'POST':
		title = request.form['title']
		content = request.form['content']
		category = request.form.get('category', 'general')
		
		new_article = Article(
			title=title,
			text=content,
			user_id=session['user_id'],
			category=category
		)
		
		db.session.add(new_article)
		db.session.commit()
		flash('Статья создана', 'success')
		return redirect(url_for('default'))
	
	return render_template('create_article.html')

@app.route('/delete-article/<int:id>')
def delete_article(id):
	if 'user_id' not in session:
		flash('Пожалуйста, войдите в систему для удаления статей', 'error')
		return redirect(url_for('login'))
	
	article = Article.query.get_or_404(id)
	
	if article.user_id != session['user_id']:
		flash('Вы можете удалять только свои статьи', 'error')
		return redirect(url_for('default'))
	
	Comment.query.filter_by(article_id=article.id).delete()
	
	db.session.delete(article)
	db.session.commit()
	
	flash('Статья успешно удалена!', 'success')
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
	
@app.route('/news/<int:id>', methods=['GET', 'POST'])
def news(id):
	article = Article.query.get_or_404(id)
	
	if request.method == 'POST':
		comment_text = request.form['comment_text']
		author_name = request.form['author_name']
		new_comment = Comment(
				text=comment_text,
				author_name=author_name,
				article_id=article.id
		)
		db.session.add(new_comment)
		db.session.commit()

		return redirect(url_for('news', id=article.id))
	
	return render_template('news.html', article=article)

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

@app.route('/api/articles', methods=['GET'])
def api_get_articles():
	category = request.args.get('category')
	sort = request.args.get('sort')
	
	query = Article.query
	
	if category:
		query = query.filter_by(category=category)
	
	if sort == 'date':
		query = query.order_by(Article.created_date.desc())
	else:
		query = query.order_by(Article.created_date.desc())
	
	articles = query.all()
	
	articles_list = []
	for article in articles:
		articles_list.append({
				'id': article.id,
				'title': article.title,
				'category': article.category,
				'created_date': article.created_date.isoformat()
		})
	
	return jsonify(articles_list)

@app.route('/api/articles', methods=['POST'])
def api_create_article():
    data = request.json
    
    if not data.get('title') or not data.get('text'):
        return jsonify({'error': 'Нужны title и text'}), 400
    
    new_article = Article(
        title=data['title'],
        text=data['text'],
        category=data.get('category', 'general'),
        user_id=session['user_id'] 
    )
    
    db.session.add(new_article)
    db.session.commit()
    
    return jsonify({
        'id': new_article.id,
        'title': new_article.title,
        'text': new_article.text,
        'category': new_article.category
    }), 201

@app.route('/api/articles/<int:id>', methods=['PUT'])
def api_update_article(id):
    article = Article.query.get(id)
    if not article:
        return jsonify({'error': 'Статья не найдена'}), 404
    
    data = request.json
    
    if not data.get('title') or not data.get('text'):
        return jsonify({'error': 'Нужны title и text'}), 400
    
    article.title = data['title']
    article.text = data['text']
    article.category = data.get('category', article.category)
    
    db.session.commit()
    
    return jsonify({
        'id': article.id,
        'title': article.title,
        'text': article.text,
        'category': article.category
    })

@app.route('/api/articles/<int:id>', methods=['DELETE'])
def api_delete_article(id):
    article = Article.query.get(id)
    if not article:
        return jsonify({'error': 'Статья не найдена'}), 404
    
    Comment.query.filter_by(article_id=id).delete()
    
    db.session.delete(article)
    db.session.commit()
    
    return jsonify({'message': 'Статья удалена'})

@app.route('/api/comment', methods=['GET'])
def api_get_comments():
	comments = Comment.query.all()
	
	comments_list = []
	for comment in comments:
		comments_list.append({
				'id': comment.id,
				'text': comment.text,
				'author_name': comment.author_name,
				'date': comment.date.isoformat(),
				'article_id': comment.article_id
		})
	
	return jsonify(comments_list)

@app.route('/api/comment/<int:id>', methods=['GET'])
def api_get_comment(id):
	comment = Comment.query.get(id)
	
	if not comment:
		return jsonify({'error': 'Комментарий не найден'}), 404
	
	comment_data = {
		'id': comment.id,
		'text': comment.text,
		'author_name': comment.author_name,
		'date': comment.date.isoformat(),
		'article_id': comment.article_id
	}
	
	return jsonify(comment_data)

@app.route('/api/comment', methods=['POST'])
def api_create_comment():
	data = request.json
	
	if not data.get('text') or not data.get('author_name') or not data.get('article_id'):
		return jsonify({'error': 'Нужны text, author_name и article_id'}), 400
	
	new_comment = Comment(
		text=data['text'],
		author_name=data['author_name'],
		article_id=data['article_id']
	)
	
	db.session.add(new_comment)
	db.session.commit()
	
	return jsonify({
		'id': new_comment.id,
		'text': new_comment.text,
		'author_name': new_comment.author_name,
		'article_id': new_comment.article_id
	}), 201

@app.route('/api/comment/<int:id>', methods=['PUT'])
def api_update_comment(id):
	comment = Comment.query.get(id)
	if not comment:
		return jsonify({'error': 'Комментарий не найден'}), 404
	
	data = request.json
	
	if not data.get('text'):
		return jsonify({'error': 'Нужен text'}), 400
	
	comment.text = data['text']
	comment.author_name = data.get('author_name', comment.author_name)
	
	db.session.commit()
	
	return jsonify({
		'id': comment.id,
		'text': comment.text,
		'author_name': comment.author_name
	})

@app.route('/api/comment/<int:id>', methods=['DELETE'])
def api_delete_comment(id):
	comment = Comment.query.get(id)
	if not comment:
		return jsonify({'error': 'Комментарий не найден'}), 404
	
	db.session.delete(comment)
	db.session.commit()
	
	return jsonify({'message': 'Комментарий удален'})

if __name__ == "__main__":
	app.run(debug=True)
