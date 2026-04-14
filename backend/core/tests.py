import pytest
from rest_framework.test import APIClient
from core.models import User, Project, Task
from datetime import date, timedelta


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="testuser@example.com",
        password="TestPass123!",
        name="Test User",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email="other@example.com",
        password="OtherPass123!",
        name="Other User",
    )


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def other_auth_client(api_client, other_user):
    client = APIClient()
    client.force_authenticate(user=other_user)
    return client


@pytest.fixture
def project(user):
    return Project.objects.create(name="Test Project", description="A test project", owner=user)


@pytest.fixture
def task(project, user):
    return Task.objects.create(
        title="Test Task",
        description="A test task",
        status=Task.STATUS.TODO,
        priority=Task.PRIORITY.HIGH,
        project=project,
        assignee=user,
        created_by=user,
        due_date=date.today() + timedelta(days=7),
    )


# ───────────────────── Auth Tests ─────────────────────


@pytest.mark.django_db
class TestRegistration:
    url = "/auth/register"

    def test_register_success(self, api_client):
        data = {"name": "Jane Doe", "email": "jane@example.com", "password": "SecurePass123!"}
        response = api_client.post(self.url, data, format="json")
        assert response.status_code == 201
        assert "token" in response.data
        assert "user" in response.data
        assert response.data["user"]["email"] == "jane@example.com"
        assert response.data["user"]["name"] == "Jane Doe"
        assert "password" not in response.data

    def test_register_duplicate_email(self, api_client, user):
        data = {"name": "Duplicate", "email": user.email, "password": "SecurePass123!"}
        response = api_client.post(self.url, data, format="json")
        assert response.status_code == 400

    def test_register_missing_fields(self, api_client):
        response = api_client.post(self.url, {}, format="json")
        assert response.status_code == 400
        assert "error" in response.data
        assert response.data["error"] == "validation failed"
        assert "name" in response.data["fields"]
        assert "email" in response.data["fields"]
        assert "password" in response.data["fields"]
        assert response.data["fields"]["name"].code == "required"
        assert response.data["fields"]["email"].code == "required"
        assert response.data["fields"]["password"].code == "required"

    def test_register_weak_password(self, api_client):
        data = {"name": "Jane", "email": "jane@example.com", "password": "123"}
        response = api_client.post(self.url, data, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestLogin:
    url = "/auth/login"

    def test_login_success(self, api_client, user):
        response = api_client.post(self.url, {"email": user.email, "password": "TestPass123!"}, format="json")
        assert response.status_code == 200
        assert "token" in response.data
        assert "user" in response.data
        assert "refresh" not in response.data

    def test_login_wrong_password(self, api_client, user):
        response = api_client.post(self.url, {"email": user.email, "password": "wrong"}, format="json")
        assert response.status_code == 401

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post(self.url, {"email": "noone@example.com", "password": "pass"}, format="json")
        assert response.status_code == 401


# ───────────────────── Project Tests ─────────────────────


@pytest.mark.django_db
class TestProjects:
    url = "/projects"

    def test_unauthenticated_access(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401

    def test_create_project(self, auth_client):
        data = {"name": "New Project", "description": "Desc"}
        response = auth_client.post(self.url, data, format="json")
        assert response.status_code == 201
        assert response.data["name"] == "New Project"

    def test_list_projects(self, auth_client, project):
        response = auth_client.get(self.url)
        assert response.status_code == 200
        assert response.data["count"] >= 1

    def test_get_project_detail(self, auth_client, project):
        response = auth_client.get(f"{self.url}/{project.id}")
        assert response.status_code == 200
        assert response.data["name"] == project.name
        assert "tasks" in response.data

    def test_update_project_non_owner_with_access_gets_403(self, other_auth_client, project, user, other_user):
        """User who has a task in the project can see it, but cannot update it (403)."""
        Task.objects.create(
            title="Assigned",
            project=project,
            assignee=other_user,
            created_by=user,
            status=Task.STATUS.TODO,
            priority=Task.PRIORITY.MEDIUM,
        )
        response = other_auth_client.patch(f"{self.url}/{project.id}", {"name": "Hacked"}, format="json")
        assert response.status_code == 403

    def test_update_project_by_owner(self, auth_client, project):
        response = auth_client.patch(f"{self.url}/{project.id}", {"name": "Updated"}, format="json")
        assert response.status_code == 200
        assert response.data["name"] == "Updated"

    def test_delete_project_non_owner_with_access_gets_403(self, other_auth_client, project, user, other_user):
        """User who has a task in the project can see it, but cannot delete it (403)."""
        Task.objects.create(
            title="Assigned",
            project=project,
            assignee=other_user,
            created_by=user,
            status=Task.STATUS.TODO,
            priority=Task.PRIORITY.MEDIUM,
        )
        response = other_auth_client.delete(f"{self.url}/{project.id}")
        assert response.status_code == 403

    def test_delete_project_by_owner(self, auth_client, project):
        response = auth_client.delete(f"{self.url}/{project.id}")
        assert response.status_code == 204

    def test_list_projects_includes_assigned(self, other_auth_client, project, user, other_user):
        """User should see projects where they have assigned tasks, not just owned ones."""
        Task.objects.create(
            title="Assigned Task",
            project=project,
            assignee=other_user,
            created_by=user,
            status=Task.STATUS.TODO,
            priority=Task.PRIORITY.MEDIUM,
        )
        response = other_auth_client.get(self.url)
        assert response.status_code == 200
        project_ids = [p["id"] for p in response.data["results"]]
        assert str(project.id) in project_ids


# ───────────────────── Task Tests ─────────────────────


@pytest.mark.django_db
class TestTasks:
    def url(self, project_id):
        return f"/projects/{project_id}/tasks"

    def task_url(self, task_id):
        return f"/tasks/{task_id}"

    def test_create_task(self, auth_client, project):
        data = {"title": "New Task", "priority": "H", "status": "T"}
        response = auth_client.post(self.url(project.id), data, format="json")
        assert response.status_code == 201
        assert response.data["title"] == "New Task"
        assert response.data["priority"] == "High"
        assert response.data["status"] == "To Do"

    def test_list_tasks(self, auth_client, project, task):
        response = auth_client.get(self.url(project.id))
        assert response.status_code == 200
        assert response.data["count"] >= 1

    def test_filter_tasks_by_status(self, auth_client, project, task):
        response = auth_client.get(self.url(project.id), {"status": "todo"})
        assert response.status_code == 200
        for t in response.data["results"]:
            assert t["status"] == "To Do"

    def test_filter_tasks_by_assignee(self, auth_client, project, task, user):
        response = auth_client.get(self.url(project.id), {"assignee_id": str(user.id)})
        assert response.status_code == 200
        assert response.data["count"] >= 1

    def test_update_task(self, auth_client, task):
        response = auth_client.patch(self.task_url(task.id), {"status": "D", "priority": "L"}, format="json")
        assert response.status_code == 200
        assert response.data["status"] == "Done"
        assert response.data["priority"] == "Low"

    def test_delete_task_by_creator(self, auth_client, task):
        response = auth_client.delete(self.task_url(task.id))
        assert response.status_code == 204

    def test_delete_task_by_non_owner(self, other_auth_client, task):
        response = other_auth_client.delete(self.task_url(task.id))
        assert response.status_code == 404

    def test_create_task_missing_title(self, auth_client, project):
        response = auth_client.post(self.url(project.id), {}, format="json")
        assert response.status_code == 400
        assert response.data["error"] == "validation failed"


# ───────────────────── Stats Tests ─────────────────────


@pytest.mark.django_db
class TestProjectStats:
    def test_stats(self, auth_client, project, user):
        Task.objects.create(
            title="T1", project=project, created_by=user, status=Task.STATUS.TODO, priority=Task.PRIORITY.LOW
        )
        Task.objects.create(
            title="T2", project=project, created_by=user, status=Task.STATUS.DONE, priority=Task.PRIORITY.HIGH
        )
        Task.objects.create(
            title="T3",
            project=project,
            created_by=user,
            assignee=user,
            status=Task.STATUS.TODO,
            priority=Task.PRIORITY.MEDIUM,
        )
        response = auth_client.get(f"/projects/{project.id}/stats")
        assert response.status_code == 200
        assert "tasks_by_status" in response.data
        assert "tasks_by_assignee_id" in response.data
