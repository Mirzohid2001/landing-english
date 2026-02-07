from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.courses, name='courses'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('teachers/', views.teachers, name='teachers'),
    path('contact/', views.contact, name='contact'),
    path('apply/', views.apply_course, name='apply_course'),
    path('videos/', views.videos, name='videos'),
    # API endpoints for AJAX
    path('api/course-video/<int:pk>/', views.get_course_video, name='get_course_video'),
    path('api/teacher-video/<int:pk>/', views.get_teacher_video, name='get_teacher_video'),
    path('api/testimonial-video/<int:pk>/', views.get_testimonial_video, name='get_testimonial_video'),
    path('api/lesson-video/<int:pk>/', views.get_lesson_video, name='get_lesson_video'),
]

