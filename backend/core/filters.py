import django_filters
from core.models import Task


class TaskFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    assignee_id = django_filters.UUIDFilter(field_name="assignee__id")
    assignee = django_filters.CharFilter(field_name="assignee__name", lookup_expr="icontains")

    class Meta:
        model = Task
        fields = ["status", "assignee", "assignee_id"]
