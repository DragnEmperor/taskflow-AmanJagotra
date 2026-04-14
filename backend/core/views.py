from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.generics import CreateAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from core import models, serializers
from core.filters import TaskFilter
from core.permissions import IsProjectOwner, IsTaskOwner


class UserRegistrationView(CreateAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = serializers.UserRegistrationSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    permission_classes = [IsProjectOwner, IsAuthenticated]

    def get_queryset(self):
        return models.Project.objects.filter(
            Q(owner=self.request.user) | Q(tasks__assignee=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProjectTaskView(ListCreateAPIView):
    serializer_class = serializers.TaskSerializer
    filterset_class = TaskFilter

    # Have allowed to create/list tasks on any project as it is not specified in the requirements
    def get_queryset(self):
        return models.Task.objects.filter(project_id=self.kwargs.get("project_id"))

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs.get("project_id"))


class TaskView(RetrieveUpdateDestroyAPIView):
    queryset = models.Task.objects.all()
    serializer_class = serializers.TaskSerializer
    permission_classes = [IsTaskOwner, IsAuthenticated]


class ProjectStatsView(APIView):
    serializer_class = serializers.ProjectStatsSerializer

    def get(self, request, project_id, *args, **kwargs):
        data = {"project_id": project_id}
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
