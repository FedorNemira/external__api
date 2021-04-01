from django.contrib import admin

from user_profile.models import UserProfile, SheduledMessage


class UserProfileAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "telegram_id")
    search_fields = ("id",)


admin.site.register(UserProfile, UserProfileAdmin)


class SheduledMessageAdmin(admin.ModelAdmin):
    
    list_display = ("user_profile", "telegram_chat_id", "text", "schedule_time", "creation_date")
    search_fields = ("id",)


admin.site.register(SheduledMessage, SheduledMessageAdmin)
