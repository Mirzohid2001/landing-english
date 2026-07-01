from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from blog.models import Course, StudentResult, Video

MINIMAL_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
    b'\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)


def make_student(**kwargs):
    defaults = {
        'first_name': 'Test',
        'last_name': 'Student',
        'bio': 'Bio',
        'is_active': True,
        'photo': SimpleUploadedFile('student.png', MINIMAL_PNG, content_type='image/png'),
    }
    defaults.update(kwargs)
    return StudentResult.objects.create(**defaults)


class VideoPageTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(
            title='IELTS Intensive',
            description='Test course',
            duration='3 months',
            price='1500000.00',
            level='intermediate',
        )
        self.youtube_video = Video.objects.create(
            title='Writing Task 2 Demo',
            description='Demo lesson',
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            video_type='course_lesson',
            course=self.course,
            is_active=True,
        )
        self.file_video = Video.objects.create(
            title='Speaking Practice',
            description='Local file lesson',
            video_url='',
            video_type='course_lesson',
            is_active=True,
        )

    def test_videos_page_renders_inline_video_data(self):
        response = self.client.get(reverse('blog:videos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'video-preview--clickable')
        self.assertContains(response, 'data-video-url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"')
        self.assertContains(response, 'id="video-modal"')
        self.assertContains(response, 'video-modal-content')

    def test_videos_page_does_not_require_ajax_data_video_id_on_play_button(self):
        response = self.client.get(reverse('blog:videos'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'data-video-id="')


class VideoApiFallbackTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.video = Video.objects.create(
            title='API Fallback Lesson',
            video_url='https://youtu.be/dQw4w9WgXcQ',
            video_type='other',
            is_active=True,
        )
        self.student = make_student(
            first_name='Ali',
            last_name='Valiyev',
            bio='IELTS 7.5',
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            is_featured=True,
        )

    def test_lesson_video_api_returns_success(self):
        response = self.client.get(reverse('blog:get_lesson_video', args=[self.video.pk]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['video_url'], 'https://youtu.be/dQw4w9WgXcQ')

    def test_lesson_video_api_not_found(self):
        response = self.client.get(reverse('blog:get_lesson_video', args=[99999]))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()['success'])

    def test_student_video_api_returns_success(self):
        response = self.client.get(reverse('blog:get_student_video', args=[self.student.pk]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('youtube.com', data['video_url'])


class HomePageCoursesLayoutTests(TestCase):
    def setUp(self):
        self.client = Client()
        Course.objects.create(
            title='Single IELTS Course',
            description='Full description',
            duration='Umrbod',
            price='599000.00',
            level='intermediate',
        )

    def test_single_course_uses_centered_grid_class(self):
        response = self.client.get(reverse('blog:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'courses-grid courses-grid--single')

    def test_courses_section_after_testimonials(self):
        content = self.client.get(reverse('blog:home')).content.decode()
        testimonials_pos = content.find('testimonials-section')
        courses_pos = content.find('courses-section')
        faq_pos = content.find('faq-section')
        self.assertGreater(courses_pos, testimonials_pos)
        if faq_pos != -1:
            self.assertLess(courses_pos, faq_pos)


class HomePageVideoTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        Video.objects.create(
            title='Home Demo',
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            video_type='promo',
            is_active=True,
        )
        make_student(
            first_name='Sara',
            last_name='Karimova',
            bio='IELTS 8.0',
            video_url='https://youtu.be/dQw4w9WgXcQ',
            is_featured=True,
        )

    def test_home_page_includes_clickable_video_previews(self):
        response = self.client.get(reverse('blog:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'video-preview-home video-preview--clickable')
        self.assertContains(response, 'student-video-overlay video-preview--clickable')
        self.assertContains(response, 'data-video-url=')


class StudentsPageVideoTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        make_student(
            first_name='Jasur',
            last_name='Toshmatov',
            bio='IELTS 7.0',
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        )

    def test_students_page_uses_inline_video_data(self):
        response = self.client.get(reverse('blog:students'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'student-video-overlay video-preview--clickable')
        self.assertContains(response, 'data-video-url=')
        self.assertNotContains(response, 'Student video handling')
