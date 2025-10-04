from flask import Flask, render_template, request

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
	


		 
@app.route('/')
def default():
	return render_template('Web.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/contact')
def contact():
	return render_template('contact.html')

if __name__ == "__main__":
	app.run()
