from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView
from core import views
from rest_framework import routers

rtr = routers.SimpleRouter(trailing_slash=False)
rtr.register("projects", views.ProjectViewSet, "projects")

urlpatterns = [
    # Authentication-related views
    path("", include(rtr.urls)),
    path("auth/login", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/register", views.UserRegistrationView.as_view(), name="user_registration"),
    path("projects/<uuid:project_id>/tasks", views.ProjectTaskView.as_view(), name="project_tasks"),
    path("tasks/<uuid:pk>", views.TaskView.as_view(), name="task_detail"),
]
