from django.contrib import admin
from .models import (
    Course, Teacher, Testimonial, Video, ContactRequest,
    CourseApplication, About, Feature, IELTSCertificate, FAQ, ProcessStep
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'level', 'price', 'duration', 'is_featured', 'created_at']
    list_filter = ['level', 'is_featured', 'created_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {}
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'level', 'duration', 'price', 'image', 'is_featured')
        }),
        ('Video Content', {
            'fields': ('promo_video_file',),
            'description': 'Upload a local video file (MP4, WebM, etc.)'
        }),
    )


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialization', 'experience', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'specialization', 'bio']
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'photo', 'bio', 'specialization', 'experience', 'is_active')
        }),
        ('Video Content', {
            'fields': ('video_file',),
            'description': 'Upload a local video file (MP4, WebM, etc.)'
        }),
    )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'rating', 'course', 'is_featured', 'created_at']
    list_filter = ['rating', 'is_featured', 'course', 'created_at']
    search_fields = ['student_name', 'text']
    fieldsets = (
        ('Student Information', {
            'fields': ('student_name', 'student_photo', 'text', 'rating', 'course', 'is_featured')
        }),
        ('Video Content', {
            'fields': ('video_file',),
            'description': 'Upload a local video file (MP4, WebM, etc.)'
        }),
    )


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'video_type', 'course', 'order', 'is_active', 'created_at']
    list_filter = ['video_type', 'is_active', 'course', 'created_at']
    search_fields = ['title', 'description']
    fieldsets = (
        ('Video Information', {
            'fields': ('title', 'description', 'video_type', 'course', 'order', 'is_active')
        }),
        ('Video Content', {
            'fields': ('video_url', 'video_file', 'preview_image'),
        }),
    )


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'is_processed', 'created_at']
    list_filter = ['is_processed', 'created_at']
    search_fields = ['name', 'email', 'phone', 'message']
    readonly_fields = ['created_at']
    list_editable = ['is_processed']


@admin.register(CourseApplication)
class CourseApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'course', 'status', 'created_at']
    list_filter = ['status', 'course', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at']
    list_editable = ['status']


@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    list_display = ['title', 'updated_at']
    fieldsets = (
        ('Content', {
            'fields': ('title', 'text', 'mission', 'achievements', 'image')
        }),
        ('Video Content', {
            'fields': ('video_file',),
            'description': 'Upload a local video file (MP4, WebM, etc.)'
        }),
    )


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['title', 'icon', 'order', 'is_active']
    list_filter = ['is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'description']


@admin.register(IELTSCertificate)
class IELTSCertificateAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'ielts_score', 'course', 'date_obtained', 'show_on_homepage', 'created_at']
    list_filter = ['show_on_homepage', 'course', 'date_obtained', 'created_at']
    search_fields = ['student_name']
    list_editable = ['show_on_homepage']
    fieldsets = (
        ('Student Information', {
            'fields': ('student_name', 'student_photo', 'ielts_score', 'date_obtained', 'course', 'show_on_homepage')
        }),
        ('Certificate', {
            'fields': ('certificate_image',),
        }),
    )


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['question', 'answer']
    list_editable = ['order', 'is_active']
    fieldsets = (
        ('FAQ Content', {
            'fields': ('question', 'answer', 'order', 'is_active')
        }),
    )


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ['step_number', 'title', 'icon', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['order', 'is_active']
    fieldsets = (
        ('Step Information', {
            'fields': ('step_number', 'title', 'description', 'icon', 'order', 'is_active')
        }),
    )
