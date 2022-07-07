# About

This is a very basic example of how to use and setup `fastapi-login`.

Please not that security is not the main focus of this example but rather showcasing how ``fastapi-login`` can be used.

# Run

In order to run this example you need to

- Install the requirements

```
$ pip install -r requirements.txt
```

- Create secret

```
$ python create_dotenv.py
```

- Run the app

```
$ uvicorn app:app --host 0.0.0.0
```

- Open ``localtest.me:8080/`` in your browser

**Important: you need to open the page with this domain name (hardcoded in the main.py). Ofc, you need to add the line 127.0.0.1 localtest.me in your /etc/host**.

login: johndoe

password: test

```
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2a$12$6mv6Z8zF2KuAtHN5H4FL9ed2gMpGdoVyy47xHe6wTasxYlvz3YEpS",
        "disabled": False,
    }
}
```



to login, navigate to: http://localtest.me:8080/login_basic

to test a protected page: http://localtest.me:8080/users/me/



To generate a new password: https://bcrypt-generator.com/