# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from dynamic_models.models import ModelSchema, FieldSchema
from django.core.exceptions import ValidationError
from django.db import transaction, connection, models
from django.conf import settings

FIELD_TYPE_MAPPING = {
    'string': 'character',
    'integer': 'integer',
    'boolean': 'boolean'
}

@api_view(['POST'])
def create_dynamic_table(request):
    table_name = request.data.get('table_name')
    fields = request.data.get('fields')

    if not table_name or not fields:
        return Response(
            {'error': 'Please provide table_name and fields in the request body.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if the table already exists
    if ModelSchema.objects.filter(name=table_name).exists():
        return Response(
            {'error': f'Table "{table_name}" already exists.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create a new instance of ModelSchema to generate the dynamic model
    try:
        with transaction.atomic():
            model_schema = ModelSchema.objects.create(name=table_name)
            dynamic_model = model_schema.as_model()
            for field in fields:
                name = field.get('name')
                field_type = field.get('type')
                data_type = FIELD_TYPE_MAPPING.get(field_type)
                if not data_type:
                    raise ValidationError(f'Invalid field type: {field_type}. Supported types are "string", "integer", and "boolean".')
                
                FieldSchema.objects.create(model_schema=model_schema, name=name, data_type=data_type)

            # Regenerate the model class after new fields are added
            try:
                dynamic_model = model_schema.as_model()
            except ValidationError as e:
                return Response(
                    {'error': f'Invalid model fields: {e}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                            
    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Error creating table: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {'message': f'Table "{table_name}" created successfully!'},
        status=status.HTTP_201_CREATED
    )

@api_view(['PUT'])
def update_dynamic_table(request, id):
    try:
        model_schema = ModelSchema.objects.get(id=id)
    except ModelSchema.DoesNotExist:
        return Response(
            {'error': 'Table with the provided ID does not exist.'},
            status=status.HTTP_404_NOT_FOUND
        )

    fields = request.data.get('fields')
    if not fields:
        return Response(
            {'error': 'Please provide fields in the request body to update the model.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            # Get the existing field names in the model schema
            existing_field_names = set(model_schema.fields.values_list('name', flat=True))

            for field in fields:
                name = field.get('name')
                field_type = field.get('type')
                if not name or not field_type:
                    return Response(
                        {'error': 'Invalid field data. Each field should have a name and a type.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                data_type = FIELD_TYPE_MAPPING.get(field_type)
                if not data_type:
                    return Response(
                        {'error': f'Invalid field type: {field_type}. Supported types are "string", "integer", and "boolean".'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Check if the field already exists in the model schema
                existing_field = FieldSchema.objects.filter(model_schema=model_schema, name=name).first()
                if existing_field:
                    # Update existing field's type if it has changed
                    if existing_field.data_type != data_type:
                        existing_field.data_type = data_type
                        existing_field.save()
                    # Remove the field name from the existing_field_names set as it's already handled
                    existing_field_names.discard(name)
                else:
                    # Create a new field if it doesn't exist
                    FieldSchema.objects.create(model_schema=model_schema, name=name, data_type=data_type)

            # Remove any fields that are present in the model schema but not in the request data
            if settings.ALLOW_FIELD_DELETION:
                FieldSchema.objects.filter(model_schema=model_schema, name__in=existing_field_names).delete()

                dynamic_model = model_schema.as_model()
                with connection.schema_editor() as schema_editor:
                    for field_name_to_remove in existing_field_names:
                        schema_editor.remove_field(dynamic_model, dynamic_model._meta.get_field(field_name_to_remove))

            # Regenerate the model class after the update
            try:
                dynamic_model = model_schema.as_model()
            except ValidationError as e:
                return Response(
                    {'error': f'Invalid model fields: {e}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
    except Exception as e:
        return Response(
            {'error': f'Error updating table: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {'message': f'Table structure for table with ID {id} updated successfully!'},
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
def add_row_to_dynamic_table(request, id):
    try:
        # Validate the input
        fields_data = request.data.get('fields')
        if not fields_data or not isinstance(fields_data, dict):
            return Response(
                {'error': 'Invalid fields data. Expected a dictionary with field names and values.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the dynamic model
        try:
            model_schema = ModelSchema.objects.get(id=id)
        except ModelSchema.DoesNotExist:
            return Response(
                {'error': 'Table with the provided ID does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )

        dynamic_model = model_schema.as_model()

        # Step 4: Create the new row
        new_row = dynamic_model(**fields_data)
        new_row.save()

        # Step 6: Return the response
        return Response(
            {'message': 'New row added successfully!'},
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        # Step 5: Handle errors
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_all_rows_in_dynamic_table(request, id):
    try:
        model_schema = ModelSchema.objects.get(id=id)
    except ModelSchema.DoesNotExist:
        return Response(
            {'error': 'Table with the provided ID does not exist.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Regenerate the model class to ensure any changes to the table structure are reflected
    try:
        dynamic_model = model_schema.as_model()
    except Exception as e:
        return Response(
            {'error': f'Error regenerating dynamic model: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Retrieve all rows from the database for the dynamically generated model
    try:
        rows = dynamic_model.objects.all()
    except Exception as e:
        return Response(
            {'error': f'Error retrieving rows from the dynamic model: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Serialize the rows and return the response
    serialized_rows = []
    for row in rows:
        serialized_row = {
            field.name: getattr(row, field.name) for field in dynamic_model._meta.fields
        }
        serialized_rows.append(serialized_row)

    return Response(serialized_rows, status=status.HTTP_200_OK)