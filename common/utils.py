from .models import Tag


def assign_tags_to_object(obj, tag_names, user):
    """Assign tags to an object, creating them if they don't exist."""
    tags = Tag.bulk_create_from_names(tag_names, created_by=user)
    obj.tags.set(tags)
    return tags
