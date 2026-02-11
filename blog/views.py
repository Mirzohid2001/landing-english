from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
import json

from .models import (
    Course, Teacher, Testimonial, Video, ContactRequest,
    CourseApplication, About, Feature, IELTSCertificate, FAQ, ProcessStep, StudentResult
)
from .forms import ContactForm, CourseApplicationForm
from .telegram_bot import send_telegram_message, format_contact_message, format_course_application_message


def home(request):
    """Главная страница с hero секцией, курсами, о'quvchilar natijalari, отзывами"""
    featured_courses = Course.objects.filter(is_featured=True)[:6]
    all_courses = Course.objects.all()[:6]
    featured_students = StudentResult.objects.filter(is_active=True, is_featured=True)[:6]
    featured_testimonials = Testimonial.objects.filter(is_featured=True)[:6]
    features = Feature.objects.filter(is_active=True)
    certificates = IELTSCertificate.objects.filter(show_on_homepage=True)[:8]
    videos = Video.objects.filter(is_active=True)[:6]  # Последние активные видео для главной страницы
    about = About.objects.first()
    faqs = FAQ.objects.filter(is_active=True)
    process_steps = ProcessStep.objects.filter(is_active=True)
    
    context = {
        'featured_courses': featured_courses,
        'courses': all_courses,
        'students': featured_students,
        'testimonials': featured_testimonials,
        'features': features,
        'certificates': certificates,
        'videos': videos,
        'about': about,
        'faqs': faqs,
        'process_steps': process_steps,
    }
    return render(request, 'index.html', context)


def courses(request):
    """Список всех курсов"""
    level_filter = request.GET.get('level', '')
    search_query = request.GET.get('search', '')
    
    courses_list = Course.objects.all()
    
    if level_filter:
        courses_list = courses_list.filter(level=level_filter)
    
    if search_query:
        courses_list = courses_list.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    paginator = Paginator(courses_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'courses': page_obj,
        'level_filter': level_filter,
        'search_query': search_query,
        'level_choices': Course.LEVEL_CHOICES,
    }
    return render(request, 'courses.html', context)


def course_detail(request, pk):
    """Детальная страница курса"""
    course = get_object_or_404(Course, pk=pk)
    lesson_videos = Video.objects.filter(course=course, is_active=True)
    related_courses = Course.objects.exclude(pk=pk)[:3]
    testimonials = Testimonial.objects.filter(course=course)[:3]
    
    context = {
        'course': course,
        'lesson_videos': lesson_videos,
        'related_courses': related_courses,
        'testimonials': testimonials,
    }
    return render(request, 'course_detail.html', context)


def students(request):
    """Bizning o'quvchilarning natijalari"""
    students_list = StudentResult.objects.filter(is_active=True)
    
    # Filter by course if provided
    course_filter = request.GET.get('course', '')
    if course_filter:
        students_list = students_list.filter(course_id=course_filter)
    
    context = {
        'students': students_list,
        'courses': Course.objects.all(),
        'course_filter': course_filter,
    }
    return render(request, 'students.html', context)


def contact(request):
    """Страница контактов"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_request = form.save()
            
            # Отправка в Telegram
            telegram_message = format_contact_message(contact_request)
            send_telegram_message(telegram_message)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you for your message! We will contact you soon.'
                })
            return redirect('contact')
    else:
        form = ContactForm()
    
    context = {
        'form': form,
    }
    return render(request, 'contact.html', context)


@require_http_methods(["POST"])
def apply_course(request):
    """Обработка заявки на курс через AJAX"""
    form = CourseApplicationForm(request.POST)
    
    if form.is_valid():
        application = form.save()
        
        # Отправка в Telegram
        telegram_message = format_course_application_message(application)
        send_telegram_message(telegram_message)
        
        return JsonResponse({
            'success': True,
            'message': f'Thank you for your application! We will contact you soon about {application.course.title}.'
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


def videos(request):
    """Страница со всеми видео"""
    video_type = request.GET.get('type', '')
    
    videos_list = Video.objects.filter(is_active=True)
    
    if video_type:
        videos_list = videos_list.filter(video_type=video_type)
    
    paginator = Paginator(videos_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'videos': page_obj,
        'video_type': video_type,
        'video_type_choices': Video.VIDEO_TYPE_CHOICES,
    }
    return render(request, 'videos.html', context)


# API endpoints for AJAX video loading
def get_course_video(request, pk):
    """API endpoint для получения видео курса"""
    try:
        course = Course.objects.get(pk=pk)
        video_file = course.promo_video_file.url if course.promo_video_file else None
        
        if not video_file:
            return JsonResponse({'success': False, 'message': 'No video available'}, status=404)
        
        return JsonResponse({
            'success': True,
            'video_url': None,
            'video_file': video_file,
            'preview_image': None,
        })
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Course not found'}, status=404)


def get_student_video(request, pk):
    """API endpoint для получения видео о'quvchi"""
    try:
        student = StudentResult.objects.get(pk=pk)
        video_file = student.video_file.url if student.video_file else None
        video_url = student.video_url if student.video_url else None
        
        if not video_file and not video_url:
            return JsonResponse({'success': False, 'message': 'No video available'}, status=404)
        
        return JsonResponse({
            'success': True,
            'video_url': video_url,
            'video_file': video_file,
        })
    except StudentResult.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student not found'}, status=404)


def get_testimonial_video(request, pk):
    """API endpoint для получения видео отзыва"""
    try:
        testimonial = Testimonial.objects.get(pk=pk)
        video_file = testimonial.video_file.url if testimonial.video_file else None
        
        if not video_file:
            return JsonResponse({'success': False, 'message': 'No video available'}, status=404)
        
        return JsonResponse({
            'success': True,
            'video_url': None,
            'video_file': video_file,
        })
    except Testimonial.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Testimonial not found'}, status=404)


def get_lesson_video(request, pk):
    """API endpoint для получения видео урока"""
    try:
        video = Video.objects.get(pk=pk)
        video_url = video.video_url if video.video_url else None
        video_file = video.video_file.url if video.video_file else None
        
        if not video_url and not video_file:
            return JsonResponse({'success': False, 'message': 'No video available'}, status=404)
        
        return JsonResponse({
            'success': True,
            'video_url': video_url,
            'video_file': video_file,
            'preview_image': video.preview_image.url if video.preview_image else None,
        })
    except Video.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Video not found'}, status=404)
