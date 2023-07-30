from django.urls import path
from .views import create_dynamic_table, update_dynamic_table, add_row_to_dynamic_table, get_all_rows_in_dynamic_table

urlpatterns = [
    # Define your app's API endpoints here
    path('table/', create_dynamic_table, name='create_dynamic_table'),
    path('table/<int:id>/', update_dynamic_table, name='update_dynamic_table'),
    path('table/<int:id>/row/', add_row_to_dynamic_table, name='add_row_to_dynamic_table'),
    path('table/<int:id>/rows/', get_all_rows_in_dynamic_table, name='get_all_rows_in_dynamic_table'),
]