from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "update-search-indexes": {
        "task": "apps.search.tasks.update_all_search_indexes",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight
    },
    "generate-sales-report": {
        "task": "apps.analytics.tasks.generate_sales_report",
        "schedule": crontab(hour=0, minute=0, day_of_month=1),  # Monthly
    },
}
