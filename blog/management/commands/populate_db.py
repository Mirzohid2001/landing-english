from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from blog.models import (
    Course, Teacher, Testimonial, Video, About, Feature, IELTSCertificate, FAQ, ProcessStep
)


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начинаю заполнение базы данных...'))

        # Создаем About
        about, created = About.objects.get_or_create(
            title="About Our English Language Center",
            defaults={
                'text': '''Welcome to our prestigious English Language Center! We are dedicated to providing 
                world-class English language education to students of all levels. With over 15 years of 
                experience, we have helped thousands of students achieve their language goals and unlock 
                new opportunities in their careers and education.''',
                'mission': '''Our mission is to empower individuals through exceptional English language 
                education, fostering global communication and cultural understanding. We believe that 
                language learning should be engaging, effective, and accessible to everyone.''',
                'achievements': '''• Over 10,000 successful graduates
                • 95% IELTS success rate
                • Award-winning teaching methodology
                • International accreditation
                • Expert native and certified teachers'''
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ About создан'))

        # Создаем Features
        features_data = [
            {
                'icon': 'fas fa-certificate',
                'title': 'Internationally Recognized',
                'description': 'Our certificates are recognized worldwide, opening doors to global opportunities.',
                'order': 1
            },
            {
                'icon': 'fas fa-users',
                'title': 'Expert Teachers',
                'description': 'Learn from experienced native speakers and certified instructors with years of expertise.',
                'order': 2
            },
            {
                'icon': 'fas fa-laptop',
                'title': 'Modern Technology',
                'description': 'State-of-the-art learning platforms and interactive digital resources for effective learning.',
                'order': 3
            },
            {
                'icon': 'fas fa-clock',
                'title': 'Flexible Schedule',
                'description': 'Choose from morning, afternoon, or evening classes that fit your busy lifestyle.',
                'order': 4
            },
            {
                'icon': 'fas fa-chart-line',
                'title': 'Proven Results',
                'description': '95% of our students achieve their target IELTS scores and language goals.',
                'order': 5
            },
            {
                'icon': 'fas fa-globe',
                'title': 'Global Community',
                'description': 'Join a diverse community of learners from around the world.',
                'order': 6
            }
        ]

        for feature_data in features_data:
            feature, created = Feature.objects.get_or_create(
                title=feature_data['title'],
                defaults=feature_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Feature "{feature.title}" создан'))

        # Создаем Teachers
        teachers_data = [
            {
                'name': 'Sarah Johnson',
                'specialization': 'IELTS Preparation & Business English',
                'experience': 12,
                'bio': '''Sarah is a native English speaker from London with over 12 years of teaching 
                experience. She specializes in IELTS preparation and has helped hundreds of students 
                achieve band scores of 7.0 and above. Her engaging teaching style makes complex grammar 
                concepts easy to understand.''',
            },
            {
                'name': 'Michael Chen',
                'specialization': 'Academic English & TOEFL',
                'experience': 10,
                'bio': '''Michael holds a Master's degree in Applied Linguistics and has been teaching 
                English for over 10 years. He is an expert in academic writing and has published several 
                research papers on language acquisition. His students consistently achieve excellent results 
                in TOEFL and academic English exams.''',
            },
            {
                'name': 'Emma Williams',
                'specialization': 'Conversational English & Pronunciation',
                'experience': 8,
                'bio': '''Emma is a certified TESOL instructor with a passion for helping students improve 
                their speaking skills. She uses innovative techniques to help students overcome pronunciation 
                challenges and build confidence in real-world conversations. Her classes are always lively 
                and interactive.''',
            },
            {
                'name': 'David Thompson',
                'specialization': 'Advanced Grammar & Writing',
                'experience': 15,
                'bio': '''David is a veteran English teacher with 15 years of experience. He has a deep 
                understanding of English grammar and helps students master even the most complex structures. 
                His writing workshops have helped countless students improve their academic and professional 
                writing skills.''',
            },
            {
                'name': 'Lisa Anderson',
                'specialization': 'English for Kids & Teens',
                'experience': 9,
                'bio': '''Lisa specializes in teaching English to children and teenagers. She creates fun, 
                engaging lessons that keep young learners motivated. Her students not only improve their 
                English but also develop a love for the language that lasts a lifetime.''',
            }
        ]

        teachers = []
        for teacher_data in teachers_data:
            teacher, created = Teacher.objects.get_or_create(
                name=teacher_data['name'],
                defaults=teacher_data
            )
            teachers.append(teacher)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Teacher "{teacher.name}" создан'))

        # Создаем Courses
        courses_data = [
            {
                'title': 'IELTS Preparation Course',
                'description': '''Comprehensive IELTS preparation course designed to help you achieve your 
                target band score. Cover all four modules: Listening, Reading, Writing, and Speaking. 
                Includes practice tests, personalized feedback, and proven strategies from experienced 
                IELTS examiners.''',
                'duration': '12 weeks',
                'price': 599.00,
                'level': 'intermediate',
                'is_featured': True,
            },
            {
                'title': 'Business English Mastery',
                'description': '''Master professional English for the workplace. Learn business vocabulary, 
                email writing, presentation skills, and negotiation techniques. Perfect for professionals 
                looking to advance their careers in international business environments.''',
                'duration': '10 weeks',
                'price': 549.00,
                'level': 'upper-intermediate',
                'is_featured': True,
            },
            {
                'title': 'English for Beginners',
                'description': '''Start your English learning journey with our comprehensive beginner course. 
                Learn essential vocabulary, basic grammar, and everyday conversation skills. Build a strong 
                foundation for further language learning in a supportive and encouraging environment.''',
                'duration': '16 weeks',
                'price': 399.00,
                'level': 'beginner',
                'is_featured': True,
            },
            {
                'title': 'Advanced English Conversation',
                'description': '''Take your speaking skills to the next level. Practice advanced conversation 
                topics, debate complex issues, and refine your pronunciation. Perfect for students who want 
                to speak English fluently and confidently in any situation.''',
                'duration': '8 weeks',
                'price': 449.00,
                'level': 'advanced',
                'is_featured': False,
            },
            {
                'title': 'Academic English Writing',
                'description': '''Master academic writing for university and research. Learn essay structure, 
                citation styles, research paper writing, and critical analysis. Essential for students 
                preparing for university studies in English-speaking countries.''',
                'duration': '14 weeks',
                'price': 649.00,
                'level': 'upper-intermediate',
                'is_featured': True,
            },
            {
                'title': 'TOEFL Preparation',
                'description': '''Comprehensive TOEFL iBT preparation course. Master all four sections: 
                Reading, Listening, Speaking, and Writing. Includes full-length practice tests and 
                personalized score improvement strategies.''',
                'duration': '10 weeks',
                'price': 599.00,
                'level': 'intermediate',
                'is_featured': False,
            },
            {
                'title': 'English for Kids (Ages 6-12)',
                'description': '''Fun and interactive English course designed specifically for children. 
                Learn through games, songs, stories, and creative activities. Build vocabulary, pronunciation, 
                and basic grammar skills while having fun!''',
                'duration': '20 weeks',
                'price': 349.00,
                'level': 'beginner',
                'is_featured': False,
            },
            {
                'title': 'Pronunciation & Accent Reduction',
                'description': '''Improve your pronunciation and reduce your accent. Learn the sounds of 
                English, stress patterns, and intonation. Perfect for professionals who want to communicate 
                more clearly and confidently.''',
                'duration': '6 weeks',
                'price': 299.00,
                'level': 'elementary',
                'is_featured': False,
            }
        ]

        courses = []
        for course_data in courses_data:
            course, created = Course.objects.get_or_create(
                title=course_data['title'],
                defaults=course_data
            )
            courses.append(course)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Course "{course.title}" создан'))

        # Создаем Videos для курсов
        video_lessons = [
            {'title': 'Introduction to IELTS', 'description': 'Learn the basics of the IELTS exam format and structure.', 'order': 1},
            {'title': 'IELTS Listening Strategies', 'description': 'Master techniques for the listening section.', 'order': 2},
            {'title': 'IELTS Reading Techniques', 'description': 'Learn how to tackle reading passages effectively.', 'order': 3},
            {'title': 'IELTS Writing Task 1', 'description': 'Master academic and general writing task 1.', 'order': 4},
            {'title': 'IELTS Writing Task 2', 'description': 'Learn to write high-scoring essays.', 'order': 5},
            {'title': 'IELTS Speaking Part 1', 'description': 'Practice common speaking topics and questions.', 'order': 6},
        ]

        ielts_course = courses[0] if courses else None
        if ielts_course:
            for lesson in video_lessons:
                video, created = Video.objects.get_or_create(
                    title=lesson['title'],
                    course=ielts_course,
                    defaults={
                        'description': lesson['description'],
                        'video_type': 'course_lesson',
                        'order': lesson['order'],
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✓ Video "{video.title}" создан'))

        # Создаем Testimonials
        testimonials_data = [
            {
                'student_name': 'Ahmad Karimov',
                'text': '''I achieved IELTS 7.5 thanks to this amazing course! The teachers are incredibly 
                supportive and the materials are comprehensive. The practice tests really helped me understand 
                what to expect on exam day.''',
                'rating': 5,
                'course': courses[0] if courses else None,
                'is_featured': True,
            },
            {
                'student_name': 'Maria Petrov',
                'text': '''The Business English course transformed my career! I now feel confident 
                communicating with international clients. The practical exercises and real-world scenarios 
                were exactly what I needed.''',
                'rating': 5,
                'course': courses[1] if len(courses) > 1 else None,
                'is_featured': True,
            },
            {
                'student_name': 'John Smith',
                'text': '''As a complete beginner, I was nervous about learning English. But the teachers 
                made it so easy and fun! Now I can have conversations in English and I'm continuing to 
                advanced levels.''',
                'rating': 5,
                'course': courses[2] if len(courses) > 2 else None,
                'is_featured': True,
            },
            {
                'student_name': 'Fatima Aliyev',
                'text': '''The Academic Writing course helped me get accepted to my dream university! 
                The feedback on my essays was detailed and constructive. I learned so much about proper 
                academic writing style.''',
                'rating': 5,
                'course': courses[4] if len(courses) > 4 else None,
                'is_featured': True,
            },
            {
                'student_name': 'David Kim',
                'text': '''Excellent TOEFL preparation! The practice tests were very similar to the real 
                exam. My score improved by 15 points after completing this course. Highly recommended!''',
                'rating': 5,
                'course': courses[5] if len(courses) > 5 else None,
                'is_featured': False,
            },
            {
                'student_name': 'Anna Volkova',
                'text': '''My daughter loved the English for Kids course! She learned so much while having 
                fun. The teachers are patient and creative. She's now confident speaking English with her 
                international friends.''',
                'rating': 5,
                'course': courses[6] if len(courses) > 6 else None,
                'is_featured': False,
            }
        ]

        for testimonial_data in testimonials_data:
            testimonial, created = Testimonial.objects.get_or_create(
                student_name=testimonial_data['student_name'],
                defaults=testimonial_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Testimonial от "{testimonial.student_name}" создан'))

        # Создаем IELTS Certificates
        certificates_data = [
            {
                'student_name': 'Ahmad Karimov',
                'ielts_score': 8.5,
                'date_obtained': date.today() - timedelta(days=30),
                'course': courses[0] if courses else None,
                'show_on_homepage': True
            },
            {
                'student_name': 'Maria Petrov',
                'ielts_score': 8.0,
                'date_obtained': date.today() - timedelta(days=45),
                'course': courses[0] if courses else None,
                'show_on_homepage': True
            },
            {
                'student_name': 'John Smith',
                'ielts_score': 7.5,
                'date_obtained': date.today() - timedelta(days=60),
                'course': courses[0] if courses else None,
                'show_on_homepage': True
            },
            {
                'student_name': 'Fatima Aliyev',
                'ielts_score': 8.0,
                'date_obtained': date.today() - timedelta(days=20),
                'course': courses[0] if courses else None,
                'show_on_homepage': True
            },
            {
                'student_name': 'David Kim',
                'ielts_score': 7.5,
                'date_obtained': date.today() - timedelta(days=75),
                'course': courses[0] if courses else None,
                'show_on_homepage': True
            },
            {
                'student_name': 'Anna Volkova',
                'ielts_score': 8.5,
                'date_obtained': date.today() - timedelta(days=15),
                'course': courses[0] if courses else None,
                'show_on_homepage': True
            },
            {
                'student_name': 'Oleg Petrov',
                'ielts_score': 7.0,
                'date_obtained': date.today() - timedelta(days=90),
                'course': courses[0] if courses else None,
                'show_on_homepage': False
            },
            {
                'student_name': 'Sara Johnson',
                'ielts_score': 8.0,
                'date_obtained': date.today() - timedelta(days=10),
                'course': courses[0] if courses else None,
                'show_on_homepage': True
            }
        ]

        for cert_data in certificates_data:
            certificate, created = IELTSCertificate.objects.get_or_create(
                student_name=cert_data['student_name'],
                defaults=cert_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Certificate для "{certificate.student_name}" создан'))

        # Создаем FAQ
        faqs_data = [
            {
                'question': 'What level of English do I need to start?',
                'answer': 'We offer courses for all levels, from complete beginners to advanced learners. You can take our free placement test to determine your current level and find the perfect course for you.',
                'order': 1
            },
            {
                'question': 'How long are the courses?',
                'answer': 'Course duration varies depending on the level and intensity. Most courses range from 8 to 16 weeks, with flexible schedules to fit your lifestyle.',
                'order': 2
            },
            {
                'question': 'Are classes online or in-person?',
                'answer': 'We offer both online and in-person classes. You can choose the format that works best for you. All online classes are conducted via our interactive platform with live teachers.',
                'order': 3
            },
            {
                'question': 'What materials do I need?',
                'answer': 'All course materials are provided digitally. You\'ll receive access to our learning platform, interactive exercises, video lessons, and downloadable resources. No additional textbooks required!',
                'order': 4
            },
            {
                'question': 'Can I get a certificate after completing the course?',
                'answer': 'Yes! Upon successful completion of your course, you\'ll receive a certificate of completion that you can add to your resume or LinkedIn profile.',
                'order': 5
            },
            {
                'question': 'What is your refund policy?',
                'answer': 'We offer a 7-day money-back guarantee. If you\'re not satisfied with your course within the first week, you can request a full refund, no questions asked.',
                'order': 6
            }
        ]

        for faq_data in faqs_data:
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults=faq_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ FAQ "{faq.question}" создан'))

        # Создаем Process Steps
        process_steps_data = [
            {
                'step_number': 1,
                'title': 'Sign Up',
                'description': 'Create your account and choose your preferred course level',
                'icon': 'fas fa-user-plus',
                'order': 1
            },
            {
                'step_number': 2,
                'title': 'Assessment',
                'description': 'Take our free placement test to determine your current level',
                'icon': 'fas fa-clipboard-check',
                'order': 2
            },
            {
                'step_number': 3,
                'title': 'Learn',
                'description': 'Start learning with expert teachers in interactive classes',
                'icon': 'fas fa-chalkboard-teacher',
                'order': 3
            },
            {
                'step_number': 4,
                'title': 'Excel',
                'description': 'Track your progress and achieve your English goals',
                'icon': 'fas fa-trophy',
                'order': 4
            }
        ]

        for step_data in process_steps_data:
            step, created = ProcessStep.objects.get_or_create(
                step_number=step_data['step_number'],
                defaults=step_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Process Step "{step.title}" создан'))

        self.stdout.write(self.style.SUCCESS('\n✓ База данных успешно заполнена!'))
        self.stdout.write(self.style.SUCCESS(f'Создано: {len(courses)} курсов, {len(teachers)} преподавателей, {len(testimonials_data)} отзывов, {len(certificates_data)} сертификатов, {len(faqs_data)} FAQ, {len(process_steps_data)} Process Steps'))

