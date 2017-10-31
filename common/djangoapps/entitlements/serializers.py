from rest_framework import serializers
from .models import CourseEntitlement
from django.contrib.auth.models import User


# class CourseEntitlementSerializer(serializers.Serializer):
#     id = serializers.IntegerField(read_only=True)
#     user = serializers.SerializerMethodField('get_username', read_only=False)
#     uuid = serializers.UUIDField(required=False)
#     course_uuid = serializers.UUIDField()
#     expired_at = serializers.DateTimeField(required=False)
#     created = serializers.DateTimeField(required=False)
#     modified = serializers.DateTimeField(required=False)
#     mode = serializers.CharField(max_length=100)
#     enrollment = serializers.SerializerMethodField('get_course_run_key')
#     order_number = serializers.CharField(max_length=128)
#
#     def get_username(self, model):
#         """Retrieves the username from the associated model."""
#         return model.user.username
#
#     def get_course_run_key(self, model):
#         if model.enrollment_course_run is not None:
#             return model.enrollment_course_run.course_id
#         else:
#             return None
#
#     # def validate(self, attrs):
#     #     print attrs
#     #
#     # def validate_user(self, value):
#     #     print(value)
#
#     def create(self, validated_data):
#         """
#         Create and return a new CourseEntitlement instance, given the validated data.
#         """
#         # username = validated_data.pop('user')
#         # user = User.objects.get(username=username)
#         # validated_data['user'] = user
#         return CourseEntitlement.objects.create(**validated_data)

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
