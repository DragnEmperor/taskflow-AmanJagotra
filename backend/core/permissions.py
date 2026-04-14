from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsProjectOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsTaskOwner(BasePermission):
    # as per requirements only creator or project owner can delete the task, anyone can update it
    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE":
            return obj.created_by == request.user or obj.project.owner == request.user
        return True
