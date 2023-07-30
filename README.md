# Task description

The goal is to build a simple backend for a table builder app, where the user can build tables dynamically. The app has the following endpoints:

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

## API Endpoints

| Request Type | Endpoint                    | Action                                                                                              |
|--------------|-----------------------------|-----------------------------------------------------------------------------------------------------|
| POST         | /api/table                  | Generate dynamic Django model based on user provided fields types and titles. The field type can be a string, number, or Boolean. HINT: you can use Python type function to generate models on the fly and the schema editor to make schema changes just like the migrations   |
| PUT          | /api/table/:id              | This end point allows the user to update the structure of dynamically generated model.             |
| POST         | /api/table/:id/row          | Allows the user to add rows to the dynamically generated model while respecting the model schema   |
| GET          | /api/table/:id/rows         | Get all the rows in the dynamically generated model                                                |

## API Documentation

Below is the documentation for the API endpoints:

### Create Dynamic Table

**Endpoint:** `POST /api/table`

**Description:** Create a dynamic table with the given table name and fields.

**Request Body:**
```json
{
  "table_name": "YourTableName",
  "fields": [
    {"name": "field1", "type": "string"},
    {"name": "field2", "type": "integer"},
    {"name": "field3", "type": "boolean"}
  ]
}
```
**Responses:**

- `201 Created`: Table created successfully!
- `400 Bad Request`: Invalid request.
- `500 Internal Server Error`: Error creating the table.


### Update Dynamic Table

**Endpoint:** `PUT /api/table/{id}`

**Description:** Update the structure of a dynamic table.

**URL Parameters:**
- `id`: ID of the dynamic table.

**Request Body:**
```json
{
  "fields": [
    {"name": "field1", "type": "string"},
    {"name": "field2", "type": "boolean"},
    {"name": "new_field_4", "type": "integer"},
    {"name": "new_field_5", "type": "string"}
  ]
}
```

**Responses:**

- `200 OK`: Table structure updated successfully!
- `400 Bad Request`: Invalid request or table with the specified ID not found.
- `500 Internal Server Error`: Error updating the table.


### Add Row to Dynamic Table

**Endpoint:** `POST /api/table/{id}/row`

**Description:** Add a new row to a dynamic table.

**URL Parameters:**
- `id`: ID of the dynamic table.

**Request Body:**
```json
{
  "fields": {
    "field1": "Value1",
    "field2": 42,
    "field3": true
  }
}
```

**Responses:**

- `201 Created`: New row added successfully!
- `400 Bad Request`: Invalid request or table with the specified ID not found.
- `500 Internal Server Error`: Error adding the row.

### Get All Rows in Dynamic Table

**Endpoint:** `GET /api/table/{id}/rows`

**Description:** Retrieve all rows from a dynamic table.

**URL Parameters:**
- `id`: ID of the dynamic table.

**Responses:**
- `200 OK`: Successful response with the array of rows.
- `404 Not Found`: Table with the specified ID not found.

## Installation

1. Clone the repository to your local machine and change to the project directory.

2. Create and activate a virtual environment (optional but recommended):

    ```
    python -m venv venv
    source venv/bin/activate # On Windows: venv\Scripts\activate
    ```
3. Install the required packages from the `requirements.txt` file:
    ```
    pip install -r requirements.txt
    ```

4. Create a .env file in the project root directory and add the necessary environment variables. For example:
    ```
    SECRET_KEY=mysecretkey
    DB_NAME=table_builder_db
    DB_USER=table_builder_user
    DB_PASSWORD=mypassword
    DB_HOST=localhost
    DB_PORT=5432
    ```
4. Apply the database migrations:
    ```
    python manage.py migrate
    ```

5. Run the development server:
    ```
    python manage.py runserver
    ```
    The Django development server will start, and you should be able to access the application at `http://localhost:8000/`.

6. Run the following command to create a superuser:
    ```
    python manage.py createsuperuser
    ```
    You will be prompted to enter a username, email address, and password for the superuser. After entering the required information, the superuser will be created and you can login at django admin page at: `http://localhost:8000/admin/`

## Configuration Options

### ALLOW_FIELD_DELETION

- **Description:** Allow deletion of fields from the dynamic model.

- **Default Value:** `True`

The `ALLOW_FIELD_DELETION` setting controls whether fields can be deleted from the dynamic model. If set to `True`, the API PUT Endpoint will allow deleting fields from the dynamic model. If set to `False`, fields will not be deleted.

You can adjust the value of this setting in your Django settings file to customize the behavior of the dynamic model and its fields.

Example:

```python
# settings.py

ALLOW_FIELD_DELETION = True
```