from flask import Flask, render_template, request
from datetime import date
app = Flask(__name__)

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
	return f"Статья {id}"

articles = [
    {"id": 1, "title": "Первая статья", "date": "2025-10-01"},
    {"id": 2, "title": "Вторая статья", "date": "2025-10-03"},
    {"id": 3, "title": "Третья статья", "date": "2025-10-05"},
]

@app.route('/')
def default():
	today = date.today().isoformat()
	return render_template('Web.html', articles=articles, today=today)

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/contact')
def contact():
	return render_template('contact.html')

if __name__ == "__main__":
	app.run()
