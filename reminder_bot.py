import datetime
import os
import re
import uuid

import dateutil.tz
import pytz
from dateutil import parser
from django.contrib.auth.models import User
from dotenv import load_dotenv
from python_watch.functions import watch
from simple_print.functions import sprint
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

from settings import DEBUG
from user_profile.models import SheduledMessage
from user_profile.models import UserProfile

load_dotenv()
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
INTERFACE_URL = os.getenv("INTERFACE_URL")
TZ = pytz.timezone("GMT")
TZ_MOSCOW_MANUAL_OFFSET = dateutil.tz.tzoffset(None, 3 * 60 * 60)
TZ_MOSCOW = pytz.timezone("Europe/Moscow")
CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)
DEBUG = True

reply_keyboard = [
    ["Сообщение", "Дата", "Время"],
    ["Отправить"],
]

KEYBOARD_MARKUP = ReplyKeyboardMarkup(reply_keyboard)


def round_time(dt, round_to=60):
    round_to *= 60
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds + round_to / 2) // round_to * round_to
    return dt + datetime.timedelta(0, rounding - seconds, -dt.microsecond)


@watch
def schedule_message_as_str(user_data):
    facts = list()
    for key, value in user_data.items():
        if key in ["Сообщение", "Дата", "Время"]:
            facts.append(f"{key} - {value}")
    return "\n".join(facts).join(["\n", "\n"])


@watch
def rebooted(update, context):
    update.message.reply_text(
        f"Нажмите /start для отправки нового сообщения",
        reply_markup=ReplyKeyboardMarkup([["/start"]]),
    )


@watch
def start(update, context):

    telegram_id = update.message.from_user.id
    now = datetime.datetime.now(TZ_MOSCOW)
    time_now = now.strftime("%H %M")

    try:
        profile = UserProfile.objects.get(telegram_id=telegram_id)
        if not profile.uuid:
            profile.uuid = uuid.uuid4().hex
            profile.save()
    except Exception as e:
        profile = None

    if profile:
        context.user_data["profile"] = profile
    else:
        profile = UserProfile()

        try:
            new_user = User.objects.create_user(username=telegram_id, email=f"{telegram_id}@workhours.ru", password=f"{uuid.uuid4()}")
            new_user.is_active = True
            new_user.save()
        except Exception as e:
            new_user = User.objects.get(email=f"{telegram_id}@workhours.ru")

        profile = UserProfile()
        profile.user = new_user
        profile.telegram_id = telegram_id
        profile.uuid = uuid.uuid4().hex
        profile.save()
        context.user_data["profile"] = profile

    update.message.reply_text(
        f"""Добро пожаловать http://{INTERFACE_URL}/{profile.uuid}/ 
(ваша личная страница, здесь можно посмотреть календарь сообщений).\n
Время таймера московское (Cейчас у нас {time_now}).\n
Введите сообщение, укажите дату и время отправки и нажмите Отправить""",
        reply_markup=KEYBOARD_MARKUP,
    )
    return CHOOSING


@watch
def message_choice(update, context):
    text = update.message.text
    context.user_data["choice"] = text
    reply_keyboard_for_message = [
        ["Позвонить", "Написать", "Перерыв"],
    ]
    KEYBOARD_MARKUP_FOR_MESSAGE = ReplyKeyboardMarkup(reply_keyboard_for_message)
    update.message.reply_text(f"{text}?", reply_markup=KEYBOARD_MARKUP_FOR_MESSAGE)

    return TYPING_REPLY


@watch
def date_choice(update, context):

    text = update.message.text
    context.user_data["choice"] = text

    now = datetime.datetime.now(TZ_MOSCOW).strftime("%d %m")
    now_plus_day = (datetime.datetime.now(TZ_MOSCOW) + datetime.timedelta(days=1)).strftime("%d %m")
    now_plus_two_days = (datetime.datetime.now(TZ_MOSCOW) + datetime.timedelta(days=2)).strftime("%d %m")
    week = (datetime.datetime.now(TZ_MOSCOW) + datetime.timedelta(days=7)).strftime("%d %m")
    month = (datetime.datetime.now(TZ_MOSCOW) + datetime.timedelta(days=31)).strftime("%d %m")

    reply_keyboard_for_message = [[now, now_plus_day, now_plus_two_days], [week, month]]
    KEYBOARD_MARKUP_FOR_MESSAGE = ReplyKeyboardMarkup(reply_keyboard_for_message)

    update.message.reply_text("Введите дату в формате dd mm (к примеру %s)?" % datetime.datetime.now(TZ).strftime("%d %m"), reply_markup=KEYBOARD_MARKUP_FOR_MESSAGE)

    return TYPING_REPLY


@watch
def time_choice(update, context):

    text = update.message.text
    context.user_data["choice"] = text

    time_range_minutes = [2, 5, 10, 30]
    time_range_hours = [1, 2, 3, 8, 16]

    minutes = []
    hours = []

    now = datetime.datetime.now(TZ_MOSCOW)

    if "Дата" not in context.user_data or now.today().strftime("%d %m") == context.user_data["Дата"]:
        for i in time_range_minutes:
            time_str = (round_time((datetime.datetime.now(TZ_MOSCOW) + datetime.timedelta(minutes=i)), i)).strftime("%H %M")
            minutes.append(time_str)

        for i in time_range_hours:
            time_str = (round_time(datetime.datetime.now(TZ_MOSCOW) + datetime.timedelta(hours=i), 30)).strftime("%H %M")
            hours.append(time_str)

        reply_keyboard_for_message = [minutes, hours]

    else:
        reply_keyboard_for_message = [["00 00", "01 00", "05 00", "06 00"], ["07 00", "09 00", "10 00", "12 00"], ["15 00", "18 00", "21 00", "23 00"]]

    KEYBOARD_MARKUP_FOR_MESSAGE = ReplyKeyboardMarkup(reply_keyboard_for_message)

    update.message.reply_text("Введите время в формате hh mm (к примеру %s)?" % datetime.datetime.now(TZ_MOSCOW).strftime("%H %M"), reply_markup=KEYBOARD_MARKUP_FOR_MESSAGE)
    return TYPING_REPLY


@watch
def received_information(update, context):
    user_data = context.user_data
    text = update.message.text
    category = user_data["choice"]
    user_data[category] = text

    if "Время" in user_data:
        try:
            now = datetime.datetime.now(TZ_MOSCOW)
            chosen_time = user_data["Время"]
            hour, minute = int(chosen_time[:2]), int(chosen_time[2:])

            if text == datetime.datetime.today().strftime("%d %m"):
                if now.time() > datetime.time(hour, minute):
                    del user_data["Время"]

            if "Время" in user_data and "Дата" in user_data:
                if now.time() > datetime.time(hour, minute) and datetime.datetime.today().strftime("%d %m") == user_data["Дата"]:
                    user_data["Дата"] = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%d %m")

        except ValueError:
            update.message.reply_text("Ошибка! Неверный формат времени")
            del user_data["Время"]

    del user_data["choice"]

    update.message.reply_text(
        f"Ваше сообщение {schedule_message_as_str(user_data)}",
        reply_markup=KEYBOARD_MARKUP,
    )

    return CHOOSING


@watch
def done(update, context):
    user_data = context.user_data
    profile = context.user_data["profile"]

    if "choice" in user_data:
        del user_data["choice"]

    now = datetime.datetime.now(TZ)
    now_year = now.year

    if DEBUG:
        sprint(user_data, "yellow")
    try:
        message_date = parser.parse(re.sub(r"(.{3})(.+)", r"\g<2> \g<1>", user_data["Дата"])).replace(tzinfo=TZ_MOSCOW_MANUAL_OFFSET)
        if DEBUG:
            sprint(message_date)
    except Exception as e:
        print(e)
        update.message.reply_text(f"Ваше сообщение {schedule_message_as_str(user_data)}")
        update.message.reply_text(
            "Дата должна быть в формате dd mm. К примеру %s" % datetime.datetime.now(TZ_MOSCOW).strftime("%d %m"),
            reply_markup=KEYBOARD_MARKUP,
        )
        return CHOOSING

    if message_date.date() < datetime.datetime.now().date():
        if DEBUG:
            sprint(message_date.date())
            sprint(datetime.datetime.now().date())
        update.message.reply_text(f"Ваше сообщение {schedule_message_as_str(user_data)}")
        update.message.reply_text(
            f"Дата отправки должна быть выше текущей",
            reply_markup=KEYBOARD_MARKUP,
        )
        return CHOOSING

    try:
        message_time = datetime.datetime.strptime(user_data["Время"], "%H %M").replace(tzinfo=TZ_MOSCOW_MANUAL_OFFSET)
        if DEBUG:
            sprint(message_time)
    except:
        update.message.reply_text(f"Ваше сообщение {schedule_message_as_str(user_data)}")
        update.message.reply_text(
            "Время должно быть в формате hh mm. К примеру %s" % datetime.datetime.now(TZ_MOSCOW).strftime("%H %M"),
            reply_markup=KEYBOARD_MARKUP,
        )
        return CHOOSING

    schedule_time = datetime.datetime.strptime(f'{user_data["Дата"]} {now_year} {user_data["Время"]}', "%d %m %Y %H %M").replace(tzinfo=TZ_MOSCOW_MANUAL_OFFSET)
    if DEBUG:
        sprint(schedule_time)

    if schedule_time < now:
        update.message.reply_text(f"Ваше сообщение {schedule_message_as_str(user_data)}")
        update.message.reply_text(
            "Время сообщения должно быть выше текущего",
            reply_markup=KEYBOARD_MARKUP,
        )

        return CHOOSING

    update.message.reply_text(
        f"""Ваше сообщение и время отправки: {schedule_message_as_str(user_data)}\n
Нажмите /start, чтобы отправить еще одно сообщение!
Посмотреть календарь можно по ссылке http://{INTERFACE_URL}/{profile.uuid}/\n
""",
    )

    sheduled_message = SheduledMessage()
    sheduled_message.user_profile = profile
    sheduled_message.telegram_chat_id = update.message.chat_id
    sheduled_message.text = user_data["Сообщение"]
    sheduled_message.schedule_time = schedule_time
    sheduled_message.save()

    for key in ["Сообщение", "Дата", "Время"]:
        user_data.pop(key)

    return ConversationHandler.END


@watch
def main():

    updater = Updater(TELEGRAM_API_KEY)
    dispatcher = updater.dispatcher

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex("^(Сообщение)$"), message_choice),
                MessageHandler(Filters.regex("^(Дата)$"), date_choice),
                MessageHandler(Filters.regex("^(Время)$"), time_choice),
            ],
            TYPING_CHOICE: [MessageHandler(Filters.text & ~(Filters.command | Filters.regex("^Отправить$")), message_choice)],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex("^Отправить$")),
                    received_information,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex("^Отправить$"), done)],
        allow_reentry=True,
        conversation_timeout=3000,
    )

    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(MessageHandler(Filters.all, rebooted))
    updater.start_polling()
    updater.idle()
