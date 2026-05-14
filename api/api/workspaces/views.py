"""Workspaces Views"""

from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.text import slugify

from api.workspaces.models import (
    Organization,
    Workspace,
    WorkspaceMembership,
    MemberRole,
)


class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Organization.objects.filter(
                deleted=False,
                workspaces__memberships__user=self.request.user,
                workspaces__memberships__is_active=True,
            ).distinct()
            | Organization.objects.filter(
                deleted=False,
                owner=self.request.user,
            ).distinct()
        )

    def perform_create(self, serializer):
        org = serializer.save(
            owner=self.request.user,
            slug=slugify(serializer.validated_data["name"]),
        )
        # Create default workspace for the org
        workspace = Workspace.objects.create(
            organization=org,
            name="Default",
            slug="default",
            created_by=self.request.user,
        )
        # Make creator the owner
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=self.request.user,
            role=MemberRole.OWNER,
        )

    @action(detail=True, methods=["get"])
    def workspaces(self, request, pk=None):
        org = self.get_object()
        qs = org.get_active_workspaces()
        data = [
            {
                "id": str(w.id),
                "name": w.name,
                "slug": w.slug,
                "visibility": w.visibility,
                "jurisdiction": w.jurisdiction,
                "ai_provider": w.ai_provider or "platform default",
                "member_count": w.memberships.filter(is_active=True).count(),
            }
            for w in qs
        ]
        return Response(data)

    def to_representation(self, instance):
        return {
            "id": str(instance.id),
            "name": instance.name,
            "slug": instance.slug,
            "org_type": instance.org_type,
            "country": instance.country,
            "industry": instance.industry,
            "is_verified": instance.is_verified,
            "created": instance.created.isoformat(),
        }

    def get_serializer(self, *args, **kwargs):
        from rest_framework import serializers

        class OrgSerializer(serializers.ModelSerializer):
            class Meta:
                model = Organization
                fields = [
                    "name",
                    "description",
                    "org_type",
                    "industry",
                    "country",
                    "website",
                ]

        return OrgSerializer(*args, **kwargs)


class WorkspaceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Workspace.objects.filter(
            deleted=False,
            memberships__user=self.request.user,
            memberships__is_active=True,
        ).select_related("organization")

    def perform_create(self, serializer):
        workspace = serializer.save(
            created_by=self.request.user,
            slug=slugify(serializer.validated_data["name"]),
        )
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=self.request.user,
            role=MemberRole.OWNER,
        )

    def get_serializer(self, *args, **kwargs):
        from rest_framework import serializers

        class WorkspaceSerializer(serializers.ModelSerializer):
            class Meta:
                model = Workspace
                fields = [
                    "name",
                    "description",
                    "organization",
                    "visibility",
                    "jurisdiction",
                    "ai_provider",
                    "ai_model",
                ]

        return WorkspaceSerializer(*args, **kwargs)

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        workspace = self.get_object()
        if not workspace.is_member(request.user):
            return Response(
                {"error": "Not a member of this workspace"},
                status=status.HTTP_403_FORBIDDEN,
            )
        members = workspace.get_active_members()
        data = [
            {
                "id": str(m.user.id),
                "email": m.user.email,
                "name": f"{m.user.first_name} {m.user.last_name}".strip(),
                "role": m.role,
                "joined": (
                    m.invitation_accepted_at.isoformat()
                    if m.invitation_accepted_at
                    else None
                ),
            }
            for m in members
        ]
        return Response(data)

    @action(detail=True, methods=["post"])
    def invite(self, request, pk=None):
        workspace = self.get_object()
        if not workspace.can_modify(request.user):
            return Response(
                {"error": "Only admins can invite members"},
                status=status.HTTP_403_FORBIDDEN,
            )
        email = request.data.get("email")
        role = request.data.get("role", MemberRole.VIEWER)
        from api.users.models import User

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": f"No user found with email {email}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        membership, created = WorkspaceMembership.objects.get_or_create(
            workspace=workspace,
            user=user,
            defaults={"role": role, "invited_by": request.user},
        )
        if not created:
            return Response(
                {"error": "User is already a member"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"message": f"{email} added to {workspace.name} as {role}"},
            status=status.HTTP_201_CREATED,
        )
