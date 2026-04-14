from typing import Any

from rest_framework import serializers
from core import models
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from core.meta import MetaSerializer
from django.db.models import Count

User = get_user_model()


class BriefUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "name", "email")


class BaseTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        return token

    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        data = super().validate(attrs)
        data.pop("refresh", None)
        data["token"] = data.pop("access")
        user = self.user
        data["user"] = BriefUserSerializer(user).data
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    user = BriefUserSerializer(read_only=True)
    token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ("name", "email", "password", "token", "user")

    def __init__(self, instance=None, data=..., **kwargs):
        super().__init__(instance, data, **kwargs)
        for field_name in self.fields:
            if field_name not in ["user", "token"]:
                self.fields[field_name].write_only = True

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        data = BaseTokenObtainPairSerializer.get_token(user)
        return {"token": str(data.access_token), "user": user}


class TaskSerializer(MetaSerializer, serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = models.Task
        fields = "__all__"
        read_only_fields = ("meta_created_at", "meta_updated_at", "project")
        object_only_fields = ("meta_created_at", "meta_updated_at", "project", "description")
        update_fields = ("title", "description", "status", "priority", "assignee", "due_date")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["status"] = instance.get_status_display()
        data["priority"] = instance.get_priority_display()
        return data


class ProjectSerializer(MetaSerializer, serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.Project
        fields = "__all__"
        object_only_fields = ("tasks",)
        read_only_fields = ("meta_created_at",)
        update_fields = ("name", "description")


class ProjectStatsSerializer(serializers.Serializer):
    project_id = serializers.UUIDField(write_only=True)
    tasks_by_status = serializers.DictField(child=serializers.IntegerField(), read_only=True)
    tasks_by_assignee = serializers.DictField(child=serializers.IntegerField(), read_only=True)

    def validate_project_id(self, value):
        if not models.Project.objects.filter(id=value).exists():
            raise serializers.ValidationError("Project with the given ID does not exist.")
        return value

    def to_representation(self, instance):
        tasks = models.Task.objects.filter(project_id=instance["project_id"])
        tasks_by_status = tasks.values("status").annotate(count=Count("id"))
        tasks_by_assignee = tasks.values("assignee__id", "assignee__name").annotate(count=Count("id"))
        status_mapping = dict(models.Task.STATUS.choices)
        return {
            "tasks_by_status": {status_mapping[task["status"]]: task["count"] for task in tasks_by_status},
            "tasks_by_assignee_id": {str(task["assignee__id"]): task["count"] for task in tasks_by_assignee},
            "tasks_by_assignee_name": {str(task["assignee__name"]): task["count"] for task in tasks_by_assignee},
        }
