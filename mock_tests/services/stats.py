"""Mock test statistikasi — login yo'q, sessiya (session_key) bo'yicha."""
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from mock_tests.models import MockAttempt, MockTest


def get_dashboard_stats(days=7):
    now = timezone.now()
    today = now.date()
    period_start = today - timedelta(days=max(days - 1, 0))

    attempts = MockAttempt.objects.all()
    finished = attempts.filter(is_finished=True)

    daily = (
        finished.filter(finished_at__date__gte=period_start)
        .annotate(day=TruncDate('finished_at'))
        .values('day')
        .annotate(
            finished_count=Count('id'),
            unique_sessions=Count('session_key', distinct=True),
        )
        .order_by('day')
    )

    per_test = (
        MockTest.objects.filter(is_active=True)
        .annotate(
            total_attempts=Count('attempts'),
            finished_attempts=Count('attempts', filter=Q(attempts__is_finished=True)),
            in_progress=Count('attempts', filter=Q(attempts__is_finished=False)),
            unique_sessions=Count('attempts__session_key', distinct=True),
            avg_score=Avg('attempts__score_percent', filter=Q(attempts__is_finished=True)),
            avg_band=Avg('attempts__ielts_band', filter=Q(attempts__is_finished=True)),
        )
        .order_by('-finished_attempts', 'title')
    )

    by_type = (
        finished.values('test__test_type')
        .annotate(
            count=Count('id'),
            unique_sessions=Count('session_key', distinct=True),
            avg_score=Avg('score_percent'),
        )
        .order_by('-count')
    )

    type_labels = dict(MockTest.TEST_TYPES)
    daily_list = list(daily)
    max_daily_finished = max((r['finished_count'] for r in daily_list), default=1) or 1

    return {
        'generated_at': now,
        'period_days': days,
        'unique_sessions': attempts.values('session_key').distinct().count(),
        'unique_sessions_with_finish': finished.values('session_key').distinct().count(),
        'total_attempts': attempts.count(),
        'finished_attempts': finished.count(),
        'in_progress': attempts.filter(is_finished=False).count(),
        'today_started': attempts.filter(started_at__date=today).count(),
        'today_finished': finished.filter(finished_at__date=today).count(),
        'period_finished': finished.filter(finished_at__date__gte=period_start).count(),
        'avg_score': finished.aggregate(v=Avg('score_percent'))['v'],
        'avg_band': finished.filter(ielts_band__isnull=False).aggregate(v=Avg('ielts_band'))['v'],
        'daily': daily_list,
        'max_daily_finished': max_daily_finished,
        'per_test': list(per_test),
        'by_type': [
            {
                **row,
                'type_label': type_labels.get(row['test__test_type'], row['test__test_type']),
            }
            for row in by_type
        ],
    }
