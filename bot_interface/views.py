import datetime

import pytz
from django.shortcuts import render

from user_profile.models import SheduledMessage

TZ_MOSCOW = pytz.timezone("Europe/Moscow")
TZ_GMT = pytz.timezone("GMT")


def main(request):
    return render(request, "bot_interface/index.html")


def user_view(request, user_uuid):

    now = datetime.datetime.now(TZ_MOSCOW)

    if request.method == "POST":
        message_id = int(request.POST.get("message_id"))
        message = SheduledMessage.objects.filter(user_profile__uuid=user_uuid, id=message_id).first()
        if message:
            message.delete()

    messages = SheduledMessage.objects.filter(user_profile__uuid=user_uuid, schedule_time__gte=now).order_by("schedule_time")
    return render(
        request,
        "bot_interface/user_page.html",
        {
            "user_uuid": user_uuid,
            "messages": messages,
        },
    )
