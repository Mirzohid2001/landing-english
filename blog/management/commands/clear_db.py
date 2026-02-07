from django.core.management.base import BaseCommand
from blog.models import (
    Course, Teacher, Testimonial, Video, ContactRequest,
    CourseApplication, About, Feature, IELTSCertificate
)


class Command(BaseCommand):
    help = 'Очищает все данные из базы данных'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Начинаю очистку базы данных...'))
        
        # Удаляем все данные
        IELTSCertificate.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Сертификаты удалены'))
        
        Video.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Видео удалены'))
        
        Testimonial.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Отзывы удалены'))
        
        CourseApplication.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Заявки на курсы удалены'))
        
        ContactRequest.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Запросы на контакты удалены'))
        
        Course.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Курсы удалены'))
        
        Teacher.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Преподаватели удалены'))
        
        Feature.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Преимущества удалены'))
        
        About.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Информация о школе удалена'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ База данных успешно очищена!'))

