from django.core.management.base import BaseCommand
from core.models import User, Project, Task
from datetime import date, timedelta


class Command(BaseCommand):
    help = "Seed the database with test data"

    def handle(self, *args, **options):
        if User.objects.filter(email="test@example.com").exists():
            self.stdout.write(self.style.WARNING("Seed data already exists. Skipping."))
            return

        user = User.objects.create_user(email="test@example.com", password="password123", name="Test User")
        self.stdout.write(self.style.SUCCESS(f"Created user: {user.email}"))

        project = Project.objects.create(
            name="Website Redesign",
            description="Q2 redesign project for the company website",
            owner=user,
        )
        self.stdout.write(self.style.SUCCESS(f"Created project: {project.name}"))

        tasks_data = [
            {
                "title": "Design homepage mockup",
                "description": "Create wireframes and high-fidelity mockups for the new homepage",
                "status": Task.STATUS.TODO,
                "priority": Task.PRIORITY.HIGH,
                "due_date": date.today() + timedelta(days=7),
            },
            {
                "title": "Implement user authentication",
                "description": "Set up login/register flow with JWT",
                "status": Task.STATUS.IN_PROGRESS,
                "priority": Task.PRIORITY.HIGH,
                "due_date": date.today() + timedelta(days=3),
            },
            {
                "title": "Write API documentation",
                "description": "Document all REST endpoints",
                "status": Task.STATUS.DONE,
                "priority": Task.PRIORITY.LOW,
                "due_date": date.today() - timedelta(days=1),
            },
        ]

        for task_data in tasks_data:
            task = Task.objects.create(project=project, assignee=user, created_by=user, **task_data)
            self.stdout.write(self.style.SUCCESS(f"Created task: {task.title} ({task.get_status_display()})"))

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
