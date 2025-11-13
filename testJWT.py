import requests

BASE_URL = "http://localhost:5000"

def test_login():
	print("1. Получение токенов:")
	
	login_data = {
		"email": "max20060602@mail.ru",
		"password": "123"
	}
	
	response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
	result = response.json()
	
	if 'error' in result:
		print(f"Ошибка: {result['error']}")
	else:
		print(f"Успех! Получены токены:")
		print(f"Access Token: {result['access_token'][:50]}...")
		print(f"Refresh Token: {result['refresh_token'][:50]}...")
		print(f"Пользователь: {result['user']['name']}")
	
	print()

def test_get_current_user(access_token):
	print("2. Получение информации о текущем пользователе:")
	
	headers = {
		"Authorization": f"Bearer {access_token}"
	}
	
	response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
	
	try:
		result = response.json()
		if 'error' in result:
				print(f"Ошибка: {result['error']}")
		else:
				print(f"Успех! Текущий пользователь:")
				print(f"ID: {result['user']['id']}")
				print(f"Имя: {result['user']['name']}")
				print(f"Email: {result['user']['email']}")
	except Exception as e:
		print(f"Ошибка: {e}")
		print(f"Статус код: {response.status_code}")
		print(f"Текст ответа: {response.text}")
	
	print()

def test_refresh_token(refresh_token):
	print("3. Обновление access токена:")
	
	refresh_data = {
		"refresh_token": refresh_token
	}
	
	response = requests.post(f"{BASE_URL}/api/auth/refresh", json=refresh_data)
	
	try:
		result = response.json()
		if 'error' in result:
				print(f"Ошибка: {result['error']}")
		else:
				print(f"Успех! Получен новый access token:")
				print(f"New Access Token: {result['access_token'][:50]}...")
				return result['access_token']
	except Exception as e:
		print(f"Ошибка: {e}")
		print(f"Статус код: {response.status_code}")
		print(f"Текст ответа: {response.text}")
	
	print()
	return None

def test_logout(refresh_token):
	print("5. Логаут:")
	
	logout_data = {
		"refresh_token": refresh_token
	}
	
	response = requests.post(f"{BASE_URL}/api/auth/logout", json=logout_data)
	
	try:
		result = response.json()
		if 'error' in result:
				print(f"Ошибка: {result['error']}")
		else:
				print(f"Успех: {result['message']}")
	except Exception as e:
		print(f"Ошибка: {e}")
		print(f"Статус код: {response.status_code}")
		print(f"Текст ответа: {response.text}")
	
	print()

tokens = test_login()

if tokens:
	test_get_current_user(tokens['access_token'])
	
	new_access_token = test_refresh_token(tokens['refresh_token'])
	
	if new_access_token:
		print("4. Проверка нового access токена:")
		test_get_current_user(new_access_token)
	
	test_logout(tokens['refresh_token'])
	
	print("6. Попытка использовать refresh токен после логаута:")
	test_refresh_token(tokens['refresh_token'])