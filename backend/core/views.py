from rest_framework.permissions import AllowAny
from rest_framework.generics import CreateAPIView
from core.serializers import UserRegistrationSerializer
from rest_framework import viewsets
from core import models, serializers
from django.db.models import Subquery, Q
from core.filters import TaskFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView


class UserRegistrationView(CreateAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = UserRegistrationSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer

    def get_queryset(self):
        filters = Q(owner=self.request.user)
        if self.request.method == "GET":
            tasks = Subquery(models.Task.objects.filter(assignee=self.request.user).values("project_id"))
            filters |= Q(id__in=tasks)
        return models.Project.objects.filter(filters).distinct()


class ProjectTaskView(ListCreateAPIView):
    serializer_class = serializers.TaskSerializer
    filterset_class = TaskFilter

    # Have allowed to create/list tasks on any project as it is not specified in the requirements
    def get_queryset(self):
        return models.Task.objects.filter(project_id=self.kwargs.get("project_id"))

    def create(self, request, *args, **kwargs):
        request.data["project"] = self.kwargs.get("project_id")
        return super().create(request, *args, **kwargs)


class TaskView(RetrieveUpdateDestroyAPIView):
    queryset = models.Task.objects.all()
    serializer_class = serializers.TaskSerializer

    # Have allowed to update tasks on any project as it is not specified in the requirements
    def get_queryset(self):
        if self.request.method == "DELETE":
            return models.Task.objects.filter(Q(created_by=self.request.user) | Q(project__owner=self.request.user))
        return super().get_queryset()
