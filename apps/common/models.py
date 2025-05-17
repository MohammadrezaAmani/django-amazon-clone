from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

User = get_user_model()


class Tag(MPTTModel):
    """Hierarchical tags with bulk creation support."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="tags",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:  # type: ignore
        verbose_name = _("tag")
        verbose_name_plural = _("tags")
        indexes = [
            models.Index(fields=["name", "slug"]),
        ]

    class MPTTMeta:
        order_insertion_by = ["name"]

    def __str__(self):  # type: ignore
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def bulk_create_from_names(cls, names, created_by=None):
        """Bulk create tags from a list of names if they don't exist."""
        existing_tags = cls.objects.filter(name__in=names)
        existing_names = set(existing_tags.values_list("name", flat=True))
        new_tags = [
            cls(name=name, created_by=created_by, slug=slugify(name))
            for name in names
            if name not in existing_names
        ]
        created_tags = cls.objects.bulk_create(new_tags)
        return list(existing_tags) + created_tags


class Action(models.Model):
    """Generic user actions."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="actions",
    )
    action_type = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("action")
        verbose_name_plural = _("actions")
        indexes = [
            models.Index(fields=["user", "action_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.action_type} by {self.user}"


class React(models.Model):
    """Generic reactions (like Instagram likes)."""

    class ReactionType(models.TextChoices):
        LIKE = "LIKE", _("Like")
        LOVE = "LOVE", _("Love")
        HAHA = "HAHA", _("Haha")
        WOW = "WOW", _("Wow")
        SAD = "SAD", _("Sad")
        ANGRY = "ANGRY", _("Angry")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    reaction_type = models.CharField(
        max_length=20,
        choices=ReactionType.choices,
        default=ReactionType.LIKE,
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("react")
        verbose_name_plural = _("reacts")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user", "reaction_type"]),
        ]
        unique_together = ("user", "content_type", "object_id", "reaction_type")

    def __str__(self):
        return f"{self.reaction_type} by {self.user} on {self.content_object}"


class View(models.Model):
    """Records views of content by users."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="views",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("view")
        verbose_name_plural = _("views")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user", "created_at"]),
        ]
        unique_together = ("user", "content_type", "object_id")

    def __str__(self):
        return f"View by {self.user} on {self.content_object}"


class Comment(MPTTModel):
    """Hierarchical comments with media, reactions, and views support."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    text = models.TextField()
    media = models.FileField(
        upload_to="comments/media/%Y/%m/%d/",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:  # type: ignore
        verbose_name = _("comment")
        verbose_name_plural = _("comments")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user", "created_at"]),
        ]

    class MPTTMeta:
        order_insertion_by = ["created_at"]

    def __str__(self):
        return f"Comment by {self.user} on {self.content_object}"


# class Location(gis_models.Model):
#     """Advanced location model with geographical and hierarchical data."""

#     class LocationType(models.TextChoices):
#         COUNTRY = "COUNTRY", _("Country")
#         STATE = "STATE", _("State")
#         CITY = "CITY", _("City")
#         NEIGHBORHOOD = "NEIGHBORHOOD", _("Neighborhood")
#         ADDRESS = "ADDRESS", _("Address")

#     name = models.CharField(max_length=200)
#     slug = models.SlugField(max_length=200, blank=True)
#     location_type = models.CharField(
#         max_length=20,
#         choices=LocationType.choices,
#     )
#     parent = models.ForeignKey(
#         "self",
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name="children",
#     )
#     country = CountryField(null=True, blank=True)
#     coordinates = gis_models.PointField(null=True, blank=True)
#     address = models.TextField(blank=True)
#     postal_code = models.CharField(max_length=20, blank=True)
#     metadata = models.JSONField(default=dict, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         verbose_name = _("location")
#         verbose_name_plural = _("locations")
#         indexes = [
#             models.Index(fields=["name", "location_type"]),
#             models.Index(fields=["country", "postal_code"]),
#             gis_models.Index(fields=["coordinates"]),
#         ]

#     def __str__(self):
#         return f"{self.name} ({self.location_type})"

#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.name)
#         super().save(*args, **kwargs)
