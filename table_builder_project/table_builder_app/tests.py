from django.contrib.auth.models import User
from rest_framework.test import APITestCase, force_authenticate
from rest_framework import status
from django.urls import reverse
from dynamic_models.models import ModelSchema, FieldSchema
from django.db import connection
from .views import FIELD_TYPE_MAPPING

class BaseAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

    def create_dynamic_table(self, table_name, fields):
        data = {
            'table_name': table_name,
            'fields': fields,
        }
        return self.client.post('/api/table/', data, format='json')

class CreateDynamicTableAPITest(BaseAPITestCase):
    def test_create_dynamic_table_success(self):
        # Test case for successful creation of dynamic table
        data = {
            'table_name': 'MyDynamicTable',
            'fields': [
                {'name': 'field1', 'type': 'string'},
                {'name': 'field2', 'type': 'integer'},
                {'name': 'field3', 'type': 'boolean'},
            ]
        }

        response = self.client.post('/api/table/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Table "MyDynamicTable" created successfully!')

    def test_create_dynamic_table_missing_fields(self):
        # Test case for missing table_name and fields in the request body
        data = {}  # Missing 'table_name' and 'fields'
        
        response = self.client.post('/api/table/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_create_dynamic_table_invalid_field_type(self):
        # Test case for providing an invalid field type
        data = {
            'table_name': 'InvalidTable',
            'fields': [
                {'name': 'field1', 'type': 'invalid_type'},  # Invalid field type
            ]
        }

        response = self.client.post('/api/table/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_create_dynamic_table_already_exists(self):
        # Test case for trying to create a table that already exists
        # First, create a table with the same name
        table_name = 'ExistingTable'
        fields = [{'name': 'field1', 'type': 'string'}]
        self.create_dynamic_table(table_name, fields)

        # Try to create the same table again
        response = self.create_dynamic_table(table_name, fields)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], f'Table "{table_name}" already exists.')        


class UpdateDynamicTableAPITest(BaseAPITestCase):
    def test_update_dynamic_table_success(self):
        table_name = 'DynamicTable1'
        fields = [{'name': 'field1', 'type': 'string'}, {'name': 'field2', 'type': 'integer'}, {'name': 'field3', 'type': 'boolean'},]
        response = self.create_dynamic_table(table_name, fields)
        self.model_schema = ModelSchema.objects.get(name=table_name)

        data = {
            'fields': [
                {'name': 'field1', 'type': 'string'},  # Same as existing field
                {'name': 'field2', 'type': 'boolean'}, # Changing the type of field2
                {'name': 'new_field_4', 'type': 'integer'},  # Adding a new field
                {'name': 'new_field_5', 'type': 'string'},   # Adding another new field
            ]
        }

        url = reverse('update_dynamic_table', kwargs={'id': self.model_schema.id})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], f'Table structure for table with ID {self.model_schema.id} updated successfully!')

        # Assert that the changes have been made in the database
        updated_fields = FieldSchema.objects.filter(model_schema=self.model_schema)
        self.assertEqual(updated_fields.count(), 4)  # Four fields after the update

    def test_update_dynamic_table_invalid_field_type(self):
        # Test case for providing an invalid field type
        table_name = 'DynamicTable2'
        fields = [{'name': 'field1', 'type': 'string'}, {'name': 'field2', 'type': 'integer'}, {'name': 'field3', 'type': 'boolean'},]
        response = self.create_dynamic_table(table_name, fields)
        self.model_schema = ModelSchema.objects.get(name=table_name)

        data = {
            'fields': [
                {'name': 'field1', 'type': 'invalid_type'},  # Invalid field type
            ]
        }

        url = reverse('update_dynamic_table', kwargs={'id': self.model_schema.id})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

        # Assert that the table structure remains unchanged
        existing_fields = FieldSchema.objects.filter(model_schema=self.model_schema)
        self.assertEqual(existing_fields.count(), 3)  # Three fields as before
  
    def test_update_dynamic_table_invalid_request_data(self):
        # Test case for providing invalid request data
        table_name = 'DynamicTable3'
        fields = [{'name': 'field1', 'type': 'string'}, {'name': 'field2', 'type': 'integer'}, {'name': 'field3', 'type': 'boolean'},]
        response = self.create_dynamic_table(table_name, fields)
        self.model_schema = ModelSchema.objects.get(name=table_name)
        data = {
            'fields': [
                {'name': 'field1'},  # Missing 'type' for a field
                {'type': 'boolean'},  # Missing 'name' for a field
            ]
        }

        url = reverse('update_dynamic_table', kwargs={'id': self.model_schema.id})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

        # Assert that the table structure remains unchanged
        existing_fields = FieldSchema.objects.filter(model_schema=self.model_schema)
        self.assertEqual(existing_fields.count(), 3)  # Three fields as before

    def test_update_dynamic_table_not_found(self):
        table_name = 'DynamicTable4'
        fields = [{'name': 'field1', 'type': 'string'}, {'name': 'field2', 'type': 'integer'}, {'name': 'field3', 'type': 'boolean'},]
        response = self.create_dynamic_table(table_name, fields)
        self.model_schema = ModelSchema.objects.get(name=table_name)
        # Test case for table not found
        data = {
            'fields': [
                {'name': 'field1', 'type': 'string'},  # Same as existing field
            ]
        }

        url = reverse('update_dynamic_table', kwargs={'id': 999})  # Non-existing ID
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Table with the provided ID does not exist.')

        # Assert that the table structure remains unchanged
        existing_fields = FieldSchema.objects.filter(model_schema=self.model_schema)
        self.assertEqual(existing_fields.count(), 3)  # Three fields as before
    

class AddRowToDynamicTableAPITest(BaseAPITestCase):
    def test_add_row_to_dynamic_table_success(self):
        table_name = "MyDynamicTable1"
        fields = [
            {'name': 'field1', 'type': 'string'},
            {'name': 'field2', 'type': 'integer'},
            {'name': 'field3', 'type': 'boolean'},
        ]
        self.create_dynamic_table(table_name, fields)
        self.model_schema = ModelSchema.objects.get(name=table_name)
        self.url = reverse('add_row_to_dynamic_table', kwargs={'id': self.model_schema.id})

        # Test case for successful addition of a new row
        data = {
            'fields': {
                'field1': 'Value 1',
                'field2': 42,
                'field3': True,
            }
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'New row added successfully!')

        # Assert that the row has been added to the database
        dynamic_model = self.model_schema.as_model()
        rows_count = dynamic_model.objects.count()
        self.assertEqual(rows_count, 1)

    def test_add_row_to_dynamic_table_invalid_fields_data(self):
        table_name = "MyDynamicTable2"
        fields = [
            {'name': 'field1', 'type': 'string'},
            {'name': 'field2', 'type': 'integer'},
            {'name': 'field3', 'type': 'boolean'},
        ]
        self.create_dynamic_table(table_name, fields)
        self.model_schema = ModelSchema.objects.get(name=table_name)
        self.url = reverse('add_row_to_dynamic_table', kwargs={'id': self.model_schema.id})

        # Test case for providing invalid fields data (not a dictionary)
        data = {
            'fields': 'invalid_data',
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_add_row_to_dynamic_table_nonexistent_table(self):
        table_name = "MyDynamicTable3"
        fields = [
            {'name': 'field1', 'type': 'string'},
            {'name': 'field2', 'type': 'integer'},
            {'name': 'field3', 'type': 'boolean'},
        ]
        self.create_dynamic_table(table_name, fields)
        self.model_schema = ModelSchema.objects.get(name=table_name)
        self.url = reverse('add_row_to_dynamic_table', kwargs={'id': self.model_schema.id})

        # Test case for trying to add a row to a non-existent table
        url = reverse('add_row_to_dynamic_table', kwargs={'id': 9999})  # Non-existent ID
        data = {
            'fields': {
                'field1': 'Value 1',
                'field2': 42,
                'field3': True,
            }
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

class GetAllRowsInDynamicTableAPITest(BaseAPITestCase):

    def test_get_all_rows_in_dynamic_table_success(self):
        table_name = "DynamicTable1"
        fields = [
            {'name': 'field1', 'type': 'string'},
            {'name': 'field2', 'type': 'integer'},
            {'name': 'field3', 'type': 'boolean'},
        ]
        response = self.create_dynamic_table(table_name, fields)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.model_schema = ModelSchema.objects.get(name=table_name)
        dynamic_model = self.model_schema.as_model()

        # Add some rows to the dynamic table
        dynamic_model.objects.create(field1='value1', field2=42, field3=True)
        dynamic_model.objects.create(field1='value2', field2=100, field3=False)

        # Test case for successfully retrieving all rows from the dynamic table
        url = reverse('get_all_rows_in_dynamic_table', kwargs={'id': self.model_schema.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the response contains the expected number of rows and their data
        self.assertEqual(len(response.data), 2)  # Two rows in the database
        self.assertDictEqual(
            response.data[0],
            {'id': 1, 'field1': 'value1', 'field2': 42, 'field3': True}
        )
        self.assertDictEqual(
            response.data[1],
            {'id': 2, 'field1': 'value2', 'field2': 100, 'field3': False}
        )

    def test_get_all_rows_in_dynamic_table_invalid_id(self):
        table_name = "DynamicTable2"
        fields = [
            {'name': 'field1', 'type': 'string'},
            {'name': 'field2', 'type': 'integer'},
            {'name': 'field3', 'type': 'boolean'},
        ]
        response = self.create_dynamic_table(table_name, fields)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.model_schema = ModelSchema.objects.get(name=table_name)

        # Test case for providing an invalid ID for the dynamic table
        invalid_id = self.model_schema.id + 600  # Non-existing ID
        url = reverse('get_all_rows_in_dynamic_table', kwargs={'id': invalid_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

