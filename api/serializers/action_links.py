from rest_framework import serializers

from admission.api.serializers.fields import ActionLinksField, ACTION_LINKS

__all__ = [
    "ActionLinksSerializer",
]


class ActionLinksSerializer(serializers.Serializer):
    links = ActionLinksField(
        actions={
            'create_proposition': ACTION_LINKS['create_proposition'],
        }
    )
