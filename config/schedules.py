from django_celery_beat.models import CrontabSchedule, PeriodicTask


def setup_periodic_tasks():
    schedule, created = CrontabSchedule.objects.get_or_create(  # type: ignore
        minute="0",
        hour="0",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )
    PeriodicTask.objects.get_or_create(
        crontab=schedule,
        name="Check pending feedbacks",
        task="feedback.tasks.check_pending_feedbacks",
        defaults={"enabled": True},
    )
