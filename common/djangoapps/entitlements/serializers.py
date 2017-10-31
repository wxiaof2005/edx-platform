from django.contrib.auth.models import User
from rest_framework import serializers

from .models import CourseEntitlement


class CourseEntitlementSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = CourseEntitlement
        fields = (
            'id',
            'user',
            'uuid',
            'course_uuid',
            'expired_at',
            'created',
            'modified',
            'mode',
            'order_number'
        )
