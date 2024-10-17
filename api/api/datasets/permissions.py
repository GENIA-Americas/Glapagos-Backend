from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission


class IsTableAllowed(BasePermission):
    message = _("You do not have permission to access this private resource. Only the owner can access it.")
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or obj.public:
            return True
        return obj.owner == request.user