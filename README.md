# Comsoft Test Project

This project is a test Django application that uses Docker for deployment and PostgreSQL as the database.



### 1. Clone the Repository

To get started, clone the repository to your local machine:

```git clone https://github.com/shironoirL/Comsoft_test.git```
### 2. Create .env file
Create a .env file in the root of the project directory based on the .envexample file. You can use the following content for your .env file:
```
POSTGRES_DB=mydatabase
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
```

### 3. Build and Start the Docker Containers
```docker compose up```

### 4. Email setup and start fetching

Navigate to <http://127.0.0.1:8000/admin/mail_app/emailaccount/> with ```admin admin``` credentials
and add email account

<http://127.0.0.1:8000/> and click "Fetch Mails"