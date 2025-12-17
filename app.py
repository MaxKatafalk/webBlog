from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from datetime import date, datetime, timedelta
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'secret-key'

app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

db = SQLAlchemy(app)

class RefreshToken(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	token = db.Column(db.String(500), unique=True, nullable=False)
	expires_at = db.Column(db.DateTime, nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
	user = db.relationship('User', backref=db.backref('refresh_tokens', lazy=True))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(100), unique=True, nullable=False)
	hashed_password = db.Column(db.String(200), nullable=False)
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


def _ensure_str(token):
	if isinstance(token, bytes):
		return token.decode('utf-8')
	return token

def create_access_token(user_id):
	payload = {
		'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES'],
		'iat': datetime.utcnow(),
		'sub': str(user_id),
		'type': 'access'
	}
	token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
	return _ensure_str(token)

def create_refresh_token(user_id):
	expires_at = datetime.utcnow() + app.config['JWT_REFRESH_TOKEN_EXPIRES']
	
	payload = {
		'exp': expires_at,
		'iat': datetime.utcnow(),
		'sub': str(user_id),
		'type': 'refresh'
	}
	
	refresh_token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
	refresh_token = _ensure_str(refresh_token)
	
	db_refresh_token = RefreshToken(
		token=refresh_token,
		user_id=user_id,
		expires_at=expires_at
	)
	db.session.add(db_refresh_token)
	db.session.commit()
	
	return refresh_token

def verify_token(token):
	try:
		payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
		return payload
	except jwt.ExpiredSignatureError:
		return None  
	except jwt.InvalidTokenError:
		return None 

def get_user_from_token(token):
	payload = verify_token(token)
	if payload and payload.get('type') == 'access':
		try:
			return User.query.get(int(payload['sub']))
		except Exception:
			return None
	return None

def jwt_required(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		auth = request.headers.get("Authorization")

		if not auth or not auth.startswith("Bearer "):
				return jsonify({"error": "Требуется access токен"}), 401

		token = auth.split()[1]
		payload = verify_token(token)

		if not payload:
				return jsonify({"error": "Недействительный или истекший токен"}), 401

		if payload.get("type") != "access":
				return jsonify({"error": "Неверный тип токена"}), 403

		try:
			user_id = int(payload.get("sub"))
		except Exception:
			return jsonify({"error": "Неверный payload токена"}), 401

		user = User.query.get(user_id)
		if not user:
				return jsonify({"error": "Пользователь не найден"}), 404

		g.current_user = user
		return f(*args, **kwargs)
	return wrapper

@app.route('/api/articles', methods=['GET'])
@jwt_required
def api_get_articles():
	category = request.args.get('category')
	sort = request.args.get('sort')
	
	query = Article.query
	
	if category:
		query = query.filter_by(category=category)
	
	query = query.order_by(Article.created_date.desc())
	
	articles = query.all()
	
	articles_list = []
	for article in articles:
		articles_list.append({
				'id': article.id,
				'title': article.title,
				'category': getattr(article, 'category', 'general'),
				'created_date': article.created_date.isoformat()
		})
	
	return jsonify(articles_list)

@app.route('/api/articles/<int:id>', methods=['GET'])
@jwt_required
def api_get_article(id):
	article = Article.query.get(id)
	if not article:
		return jsonify({'error': 'Статья не найдена'}), 404
	
	return jsonify({
		'id': article.id,
		'title': article.title,
		'text': article.text,
		'category': getattr(article, 'category', 'general'),
		'created_date': article.created_date.isoformat(),
		'user_id': article.user_id
	})

@app.route('/api/articles', methods=['POST'])
@jwt_required
def api_create_article():
	data = request.json or {}
	
	if not g.get('current_user'):
		return jsonify({'error': 'Требуется авторизация'}), 401

	if not data.get('title') or not data.get('text'):
		return jsonify({'error': 'Нужны title и text'}), 400
	
	new_article = Article(
		title=data['title'],
		text=data['text'],
		category=data.get('category', 'general'),
		user_id=g.current_user.id
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
@jwt_required
def api_update_article(id):
	if not g.get('current_user'):
		return jsonify({'error': 'Требуется авторизация'}), 401

	article = Article.query.get(id)
	if not article:
		return jsonify({'error': 'Статья не найдена'}), 404
	
	if article.user_id != g.current_user.id:
		return jsonify({'error': 'Вы можете редактировать только свои статьи'}), 403
	
	data = request.json or {}
	
	if not data.get('title') or not data.get('text'):
		return jsonify({'error': 'Нужны title и text'}), 400
	
	article.title = data['title']
	article.text = data['text']
	article.category = data.get('category', getattr(article, 'category', 'general'))
	
	db.session.commit()
	
	return jsonify({
		'id': article.id,
		'title': article.title,
		'text': article.text,
		'category': article.category
	})

@app.route('/api/articles/<int:id>', methods=['DELETE'])
@jwt_required
def api_delete_article(id):
	if not g.get('current_user'):
		return jsonify({'error': 'Требуется авторизация'}), 401

	article = Article.query.get(id)
	if not article:
		return jsonify({'error': 'Статья не найдена'}), 404

	if article.user_id != g.current_user.id:
		return jsonify({'error': 'Вы можете удалять только свои статьи'}), 403
	
	Comment.query.filter_by(article_id=id).delete()
	
	db.session.delete(article)
	db.session.commit()
	
	return jsonify({'message': 'Статья удалена'})

@app.route('/api/comment', methods=['GET'])
@jwt_required
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
@jwt_required
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
@jwt_required
def api_create_comment():
	data = request.json or {}
	
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
@jwt_required
def api_update_comment(id):
	comment = Comment.query.get(id)
	if not comment:
		return jsonify({'error': 'Комментарий не найден'}), 404
	
	data = request.json or {}
	
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
@jwt_required
def api_delete_comment(id):
	comment = Comment.query.get(id)
	if not comment:
		return jsonify({'error': 'Комментарий не найден'}), 404
	
	db.session.delete(comment)
	db.session.commit()
	
	return jsonify({'message': 'Комментарий удален'})

@app.route('/api/auth/login', methods=['POST'])
def api_login():
	data = request.json
	
	if not data or not data.get('email') or not data.get('password'):
		return jsonify({'error': 'Требуется email и пароль'}), 400
	
	user = User.query.filter_by(email=data['email']).first()
	
	if user and user.check_password(data['password']):
		access_token = create_access_token(user.id)
		refresh_token = create_refresh_token(user.id)
		
		return jsonify({
					'access_token': access_token,
					'refresh_token': refresh_token,
					'user': {
						'id': user.id,
						'name': user.name,
						'email': user.email
					}
		}), 200
	else:
		return jsonify({'error': 'Неверный email или пароль'}), 401

@app.route('/api/auth/refresh', methods=['POST'])
def api_refresh():
	data = request.json
	
	if not data or not data.get('refresh_token'):
		return jsonify({'error': 'Требуется refresh token'}), 400
	
	refresh_token = data['refresh_token']
	
	db_refresh_token = RefreshToken.query.filter_by(token=refresh_token).first()
	
	if not db_refresh_token or db_refresh_token.expires_at < datetime.utcnow():
		return jsonify({'error': 'Невалидный или истекший refresh token'}), 401
	
	payload = verify_token(refresh_token)
	if not payload or payload.get('type') != 'refresh':
		return jsonify({'error': 'Невалидный refresh token'}), 401
	
	try:
		sub_id = int(payload['sub'])
	except Exception:
		return jsonify({'error': 'Неверный payload в refresh token'}), 401
	
	new_access_token = create_access_token(sub_id)
	
	return jsonify({
		'access_token': new_access_token
	}), 200

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
	data = request.json
	
	if not data or not data.get('refresh_token'):
		return jsonify({'error': 'Требуется refresh token'}), 400
	
	refresh_token = RefreshToken.query.filter_by(token=data['refresh_token']).first()
	if refresh_token:
		db.session.delete(refresh_token)
		db.session.commit()
	
	return jsonify({'message': 'Успешный выход из системы'}), 200

@app.route('/api/auth/me', methods=['GET'])
@jwt_required
def api_get_current_user():
	return jsonify({
		"user": {
				"id": g.current_user.id,
				"name": g.current_user.name,
				"email": g.current_user.email
		}
	}), 200

if __name__ == "__main__":
	app.run(debug=True)
