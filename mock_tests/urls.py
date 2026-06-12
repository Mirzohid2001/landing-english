from django.urls import path
from . import views

app_name = 'mock_tests'

urlpatterns = [
    path('', views.test_list, name='test_list'),
    path('tests/<int:pk>/', views.test_detail, name='test_detail'),
    path('tests/<int:pk>/take/', views.test_take, name='test_take'),
    path('tests/<int:pk>/result/<int:attempt_id>/', views.test_result, name='test_result'),
]
