"""
Glapagos Workspace Models
api/api/workspaces/models/workspace.py
"""
from __future__ import annotations
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from api.utils.models import BaseModel
from api.users.enums import Country, Industry


class OrganizationType(models.TextChoices):
    COMPANY     = "company",     _("Company")
    GOVERNMENT  = "government",  _("Government")
    UNIVERSITY  = "university",  _("University")
    NGO         = "ngo",         _("NGO / Non-profit")
    RESEARCH    = "research",    _("Research Institute")
    STARTUP     = "startup",     _("Startup")
    COOPERATIVE = "cooperative", _("Cooperative")
    OTHER       = "other",       _("Other")


class WorkspaceVisibility(models.TextChoices):
    PRIVATE  = "private",  _("Private - invitation only")
    INTERNAL = "internal", _("Internal - visible to org members")
    PUBLIC   = "public",   _("Public - visible to all Glapagos users")


class MemberRole(models.TextChoices):
    OWNER       = "owner",       _("Owner")
    ADMIN       = "admin",       _("Admin")
    CONTRIBUTOR = "contributor", _("Contributor")
    VIEWER      = "viewer",      _("Viewer")


class ComplianceJurisdiction(models.TextChoices):
    LGPD        = "lgpd",        _("Brazil - LGPD")
    MEXICO_PDPA = "mexico_pdpa", _("Mexico - Ley Federal de Proteccion de Datos")
    COLOMBIA    = "colombia",    _("Colombia - Ley 1581")
    ARGENTINA   = "argentina",   _("Argentina - PDPA")
    GDPR        = "gdpr",        _("EU - GDPR")
    CCPA        = "ccpa",        _("USA - CCPA")
    NONE        = "none",        _("No specific jurisdiction")


class Organization(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    org_type = models.CharField(max_length=20, choices=OrganizationType.choices, default=OrganizationType.COMPANY)
    industry = models.CharField(max_length=255, choices=Industry.choices, null=True, blank=True)
    country = models.CharField(max_length=255, choices=Country.choices, null=True, blank=True)
    website = models.URLField(blank=True, default="")
    logo_url = models.URLField(blank=True, default="")
    is_verified = models.BooleanField(default=False)
    owner = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="owned_organizations")

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.slug})"

    def get_owner(self):
        return self.owner

    def get_active_workspaces(self):
        return self.workspaces.filter(deleted=False)


class Workspace(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="workspaces")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True, default="")
    visibility = models.CharField(max_length=20, choices=WorkspaceVisibility.choices, default=WorkspaceVisibility.PRIVATE)
    jurisdiction = models.CharField(max_length=20, choices=ComplianceJurisdiction.choices, default=ComplianceJurisdiction.NONE)
    ai_provider = models.CharField(max_length=50, blank=True, default="")
    ai_model = models.CharField(max_length=100, blank=True, default="")
    created_by = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="created_workspaces")

    class Meta:
        verbose_name = _("Workspace")
        verbose_name_plural = _("Workspaces")
        ordering = ["organization", "name"]
        unique_together = [("organization", "slug")]

    def __str__(self):
        return f"{self.organization.slug}/{self.slug}"

    def get_owner(self):
        return self.created_by

    def get_active_members(self):
        return self.memberships.filter(is_active=True).select_related("user")

    def is_member(self, user):
        return self.memberships.filter(user=user, is_active=True).exists()

    def get_user_role(self, user):
        membership = self.memberships.filter(user=user, is_active=True).first()
        return membership.role if membership else None

    def can_modify(self, user, *args, **kwargs):
        if user.is_app_superuser():
            return True
        role = self.get_user_role(user)
        return role in [MemberRole.OWNER, MemberRole.ADMIN]


class WorkspaceMembership(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="workspace_memberships")
    role = models.CharField(max_length=20, choices=MemberRole.choices, default=MemberRole.VIEWER)
    is_active = models.BooleanField(default=True)
    invited_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_invitations")
    invitation_accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Workspace Membership")
        verbose_name_plural = _("Workspace Memberships")
        unique_together = [("workspace", "user")]
        ordering = ["workspace", "role"]

    def __str__(self):
        return f"{self.user.email} -> {self.workspace} ({self.role})"

    def get_owner(self):
        return self.user

    def can_modify(self, user, *args, **kwargs):
        if user.is_app_superuser():
            return True
        if self.workspace.get_user_role(user) in [MemberRole.OWNER, MemberRole.ADMIN]:
            return True
        return self.user == user

    @property
    def is_admin(self):
        return self.role in [MemberRole.OWNER, MemberRole.ADMIN]
