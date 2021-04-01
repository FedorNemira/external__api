from datetime import datetime

import pytz
from django.utils import timezone

from settings import POSTGRES_DB
from user_profile.models import SheduledMessage


def make_query():
    # python run.py bot_interface.tasks "make_query()"

    timezone.activate(pytz.timezone("Europe/Moscow"))
    print(POSTGRES_DB)
    month = int(datetime.today().strftime("%m"))
    day = int(datetime.today().strftime("%d"))
    hour = int(datetime.today().strftime("%H"))
    minute = int(datetime.today().strftime("%M"))

    if True:
        month = 3
        day = 21
        hour = 15
        minute = 30

    print(SheduledMessage.objects.filter(schedule_time__month=month, schedule_time__day=day, schedule_time__hour=hour, schedule_time__minute=minute))

    q = SheduledMessage.objects.filter(schedule_time__month=month, schedule_time__day=day, schedule_time__hour=hour, schedule_time__minute=minute).query
    print(q)

    q = SheduledMessage.objects.get(pk=1)
    print(q.schedule_time)
