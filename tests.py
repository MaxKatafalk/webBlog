import requests

BASE_URL = "http://localhost:5000"

def test_get_articles():
	print("1. Получение всех статей:")
	response = requests.get(f"{BASE_URL}/api/articles")
	
	articles = response.json()
	print(f"Найдено статей: {len(articles)}")
	for article in articles:
		print(f"ID: {article['id']}, Заголовок: {article['title']}")
	print()

def test_get_article_by_id(article_id):
	print("2. Получение статьи по ID:")
	
	response = requests.get(f"{BASE_URL}/api/articles/{article_id}")
	article = response.json()
	print(f"Статья: {article['title']}")
	print()

def test_create_article(title, text, category="general"):
	print("Создание статьи:")
	
	article_data = {
		"title": title,
		"text": text,
		"category": category
	}
	
	response = requests.post(f"{BASE_URL}/api/articles", json=article_data)
	article = response.json()
	print(f"Создана статья: {article['title']}")
	print()

def test_update_article(article_id, title, text, category=None):
	print("Обновление статьи:")
	
	update_data = {
		"title": title,
		"text": text
	}
	
	if category:
		update_data["category"] = category
	
	response = requests.put(f"{BASE_URL}/api/articles/{article_id}", json=update_data)
	result = response.json()
	
	if 'error' in result:
		print(f"Ошибка: {result['error']}")
	else:
		print(f"Успех: {result['title']}")
	print()

def test_delete_article(article_id):
	print("Удаление статьи:")
	
	response = requests.delete(f"{BASE_URL}/api/articles/{article_id}")
	result = response.json()
	
	if 'error' in result:
		print(f"Ошибка: {result['error']}")
	else:
		print(f"Успех: {result['message']}")
	print()

def test_get_comments():
	print("Список всех комментариев:")
	response = requests.get(f"{BASE_URL}/api/comment")
	comments = response.json()
	print(f"Найдено комментариев: {len(comments)}")
	for comment in comments:
		print(f"ID: {comment['id']}, Автор: {comment['author_name']}")
	print()

def test_get_comment_by_id(comment_id):
	print("Комментарий по ID:")
	response = requests.get(f"{BASE_URL}/api/comment/{comment_id}")
	comment = response.json()
	print(f"Комментарий: {comment['text']}")
	print()

def test_create_comment(text, author_name, article_id):
	print("Создание комментария:")
	comment_data = {
		"text": text,
		"author_name": author_name,
		"article_id": article_id
	}
	response = requests.post(f"{BASE_URL}/api/comment", json=comment_data)
	comment = response.json()
	print(f"Создан комментарий: {comment['text']}")
	print()

def test_update_comment(comment_id, text, author_name=None):
	print("Обновление комментария:")
	update_data = {"text": text}
	if author_name:
		update_data["author_name"] = author_name
	
	response = requests.put(f"{BASE_URL}/api/comment/{comment_id}", json=update_data)
	comment = response.json()
	print(f"Обновлен комментарий: {comment['text']}")
	print()

def test_delete_comment(comment_id):
	print("Удаление комментария:")
	response = requests.delete(f"{BASE_URL}/api/comment/{comment_id}")
	result = response.json()
	print(f"Результат: {result['message']}")
	print()

#test_get_articles()
#test_get_article_by_id(5)
#test_create_article("Новая статья", "Текст новой статьи", "news")
#test_update_article(5, "Обновленный заголовок", "Обновленный текст", "updated")
#test_delete_article(3)
#test_get_comments()
#test_get_comment_by_id(3)
#test_create_comment("Отличная статья!", "Читатель", 1)
#test_update_comment(1, "Обновленный комментарий")
#test_delete_comment(3)