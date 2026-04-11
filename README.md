# Updated Repository

![Diagram](diagram.png)

Managed by Agent.

### Key frameworks and technologies
* Python 3.x
* SQLAlchemy (ORM)
* Twilio (for WhatsApp integration)
* AWS Lambda (serverless function)

### Brief summary of the project
This is a Grocery List Chatbot for WhatsApp, built using Python as the primary language. It uses SQLAlchemy to interact with a PostgreSQL database, and Twilio for integrating with WhatsApp. The chatbot allows users to add, modify, delete, and list items in their grocery list.

### Contents

* [How to Run](#how-to-run)
* [Architecture](#architecture)
* [Improvements](#improvements)
* [Conclusion](#conclusion)

### How to Run
To run the chatbot, follow these steps:

1. Install the required dependencies by running `pip install -r requirements.txt` in your terminal.
2. Create a `.password` file with your PostgreSQL password and place it in the same directory as the script.
3. Run the chatbot using `python grocery_manager.py` (for local Postgres) or `python pg_grocery_manager.py` (for AWS Lambda).

```
# Local Postgres
$ python grocery_manager.py

🐘 Local Postgres Grocery Manager Initialized!
Commands: add [item] [qty] | modify [item] [qty] | delete [item] | list | exit
---------------------------

# AWS Lambda
$ python pg_grocery_manager.py
```

### Architecture
The chatbot consists of two main components:

1. **Local Postgres**: The primary database for storing and retrieving grocery list data.
2. **AWS Lambda**: A serverless function that handles WhatsApp integration and interacts with the PostgreSQL database.

The architecture is as follows:
```markdown
+---------------+
|  WhatsApp    |
+---------------+
          |
          | (API Request)
          v
+---------------+
|  AWS Lambda  |
+---------------+
          |
          | (Function Execution)
          v
+---------------+
|  PostgreSQL  |
+---------------+
```

### Improvements

1. **Error Handling**: Implement more robust error handling to handle cases where the database is unavailable or the API request fails.
2. **Security**: Add additional security measures, such as encryption and secure password storage, to protect user data.
3. **Scalability**: Optimize the code for scalability by using caching mechanisms and load balancing.

### Conclusion
Thanks for reading up until here. I had a ton of fun doing this project and got a lot of useful insights on Python, SQLAlchemy, Twilio, and AWS Lambda. If you want to see similar projects, go to my github page. Feel free to reach me on [LinkedIn](https://www.linkedin.com/in/isaiapedro/) or my [Webpage](https://github.com/isaiapedro/Portfolio-Website).