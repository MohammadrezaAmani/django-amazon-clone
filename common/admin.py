from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from .models import Action, Comment, React, Tag, View  # , Location


@admin.register(Tag)
class TagAdmin(MPTTModelAdmin):
    list_display = ("name", "slug", "parent", "created_by", "created_at")
    list_filter = ("parent", "created_by")
    search_fields = ("name", "slug")


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ("user", "action_type", "created_at")
    list_filter = ("action_type", "user")
    search_fields = ("action_type",)


@admin.register(React)
class ReactAdmin(admin.ModelAdmin):
    list_display = ("user", "reaction_type", "content_type", "object_id", "created_at")
    list_filter = ("reaction_type", "user")
    search_fields = ("user__username",)


@admin.register(View)
class ViewAdmin(admin.ModelAdmin):
    list_display = ("user", "content_type", "object_id", "created_at")
    list_filter = ("user",)
    search_fields = ("user__username",)


@admin.register(Comment)
class CommentAdmin(MPTTModelAdmin):
    list_display = ("user", "content_type", "object_id", "text", "created_at")
    list_filter = ("user", "content_type")
    search_fields = ("text",)


# @admin.register(Location)
# class LocationAdmin(admin.ModelAdmin):
#     list_display = ("name", "location_type", "country", "parent", "created_at")
#     list_filter = ("location_type", "country")
#     search_fields = ("name", "address", "postal_code")
