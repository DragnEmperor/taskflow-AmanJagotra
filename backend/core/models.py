from django.db import models
from django.contrib.auth.models import AbstractUser
from uuid import uuid7
from django.utils import timezone
from django.contrib.auth.models import UserManager


class CustomUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    first_name = last_name = username = None
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    meta_created_at = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    REQUIRED_FIELDS = ["name", "password"]
    USERNAME_FIELD = "email"

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        return self.name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.name.split()[0] if self.name else ""


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    meta_created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-meta_created_at"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class STATUS(models.TextChoices):
        TODO = "T", "To Do"
        IN_PROGRESS = "I", "In Progress"
        DONE = "D", "Done"

    class PRIORITY(models.TextChoices):
        LOW = "L", "Low"
        MEDIUM = "M", "Medium"
        HIGH = "H", "High"

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=1, choices=STATUS.choices, default=STATUS.TODO)
    priority = models.CharField(max_length=1, choices=PRIORITY.choices, default=PRIORITY.MEDIUM)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_tasks")
    meta_created_at = models.DateTimeField(default=timezone.now)
    meta_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-meta_created_at"]

    def __str__(self):
        return self.title
