# Task description

The goal is to build a simple backend for a table builder app, where the user can build tables dynamically. The app has the following endpoints:

## API Endpoints

| Request Type | Endpoint                    | Action                                                                                              |
|--------------|-----------------------------|-----------------------------------------------------------------------------------------------------|
| POST         | /api/table                  | Generate dynamic Django model based on user provided fields types and titles. The field type can be a string, number, or Boolean. HINT: you can use Python type function to generate models on the fly and the schema editor to make schema changes just like the migrations   |
| PUT          | /api/table/:id              | This end point allows the user to update the structure of dynamically generated model.             |
| POST         | /api/table/:id/row          | Allows the user to add rows to the dynamically generated model while respecting the model schema   |
| GET          | /api/table/:id/rows         | Get all the rows in the dynamically generated model                                                |

##### Requirements:
- You must build this app with Django.
- All API calls should be handled by Django REST framework.
- You must use Postgres as DB backend.
- Feel free to add test if you want!
- Write clean and Organized code.

##### You will be judged on:
- Code quality
- Organization and structure
- Following best practices on handling APIs
- Error handling