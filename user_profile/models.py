from django.contrib.auth.models import User
from django.db import models
from django.db.models.fields import DateTimeField


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    telegram_id = models.IntegerField()
    uuid = models.CharField(max_length=255, null=True, blank=True)


class SheduledMessage(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    telegram_chat_id = models.IntegerField() 
    text = models.CharField(max_length=5000)
    schedule_time = DateTimeField()
    creation_date = DateTimeField(auto_now_add=True)
