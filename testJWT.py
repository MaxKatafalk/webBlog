import requests

BASE_URL = "http://localhost:5000"


def test_login():
	print("=== ЛОГИН ===")

	login_data = {
		"email": "max20060602@mail.ru",
		"password": "123"
	}

	response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)

	try:
		result = response.json()
	except Exception:
		print("Ошибка: сервер вернул не JSON")
		print(response.text)
		return None

	if 'error' in result:
		print(f"Ошибка: {result['error']}")
		return None

	print("Успех!")
	print(f"User: {result['user']['name']}")
	print(f"Access token: {result['access_token'][:40]}...")
	print(f"Refresh token: {result['refresh_token'][:40]}...")
	print()

	return result


def test_access_without_token():
	print("=== ДОСТУП БЕЗ ТОКЕНА ===")

	response = requests.get(f"{BASE_URL}/api/articles")

	try:
		print("Ответ:", response.json())
	except Exception:
		print("Ошибка чтения ответа")

	print("Статус код:", response.status_code)
	print()


def test_access_with_token(access_token):
	print("=== ДОСТУП С ACCESS ТОКЕНОМ ===")

	headers = {
		"Authorization": f"Bearer {access_token}"
	}

	response = requests.get(f"{BASE_URL}/api/articles", headers=headers)

	try:
		result = response.json()
		if isinstance(result, list):
			print(f"Успех! Получено статей: {len(result)}")
		else:
			print("Ответ:", result)
	except Exception:
		print("Ошибка чтения ответа")

	print("Статус код:", response.status_code)
	print()


def test_create_article(access_token):
	print("=== СОЗДАНИЕ СТАТЬИ ===")

	headers = {
		"Authorization": f"Bearer {access_token}"
	}

	data = {
		"title": "JWT test article",
		"text": "Тестовая статья через JWT",
		"category": "test"
	}

	response = requests.post(
		f"{BASE_URL}/api/articles",
		headers=headers,
		json=data
	)

	try:
		result = response.json()
		if 'error' in result:
			print("Ошибка:", result['error'])
		else:
			print("Успех! Статья создана")
			print("ID:", result['id'])
			return result['id']
	except Exception:
		print("Ошибка чтения ответа")

	print("Статус код:", response.status_code)
	print()
	return None


def test_refresh_token(refresh_token):
	print("=== REFRESH ТОКЕНА ===")

	data = {
		"refresh_token": refresh_token
	}

	response = requests.post(f"{BASE_URL}/api/auth/refresh", json=data)

	try:
		result = response.json()
		if 'error' in result:
			print("Ошибка:", result['error'])
			return None
		else:
			print("Успех!")
			print(f"Новый access token: {result['access_token'][:40]}...")
			return result['access_token']
	except Exception:
		print("Ошибка чтения ответа")

	print("Статус код:", response.status_code)
	print()
	return None


def test_logout(refresh_token):
	print("=== ЛОГАУТ ===")

	data = {
		"refresh_token": refresh_token
	}

	response = requests.post(f"{BASE_URL}/api/auth/logout", json=data)

	try:
		result = response.json()
		if 'error' in result:
			print("Ошибка:", result['error'])
		else:
			print("Успех:", result['message'])
	except Exception:
		print("Ошибка чтения ответа")

	print("Статус код:", response.status_code)
	print()


tokens = test_login()

if tokens:
	test_access_without_token()
	test_access_with_token(tokens['access_token'])

	article_id = test_create_article(tokens['access_token'])

	new_access = test_refresh_token(tokens['refresh_token'])
	if new_access:
		print("Refresh работает\n")

	test_logout(tokens['refresh_token'])

	print("=== ПОПЫТКА REFRESH ПОСЛЕ ЛОГАУТА ===")
	test_refresh_token(tokens['refresh_token'])
