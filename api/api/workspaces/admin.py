"""Workspaces admin"""
from django.contrib import admin
from api.workspaces.models import Organization, Workspace, WorkspaceMembership


class WorkspaceMembershipInline(admin.TabularInline):
    model = WorkspaceMembership
    extra = 0
    fields = ["user", "role", "is_active", "invited_by", "invitation_accepted_at"]
    readonly_fields = ["invitation_accepted_at"]


class WorkspaceInline(admin.TabularInline):
    model = Workspace
    extra = 0
    fields = ["name", "slug", "visibility", "jurisdiction", "ai_provider", "deleted"]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "org_type", "country", "is_verified", "created"]
    list_filter = ["org_type", "country", "industry", "is_verified"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [WorkspaceInline]
    readonly_fields = ["created", "modified"]


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ["name", "organization", "visibility", "jurisdiction", "ai_provider", "created"]
    list_filter = ["visibility", "jurisdiction", "ai_provider", "deleted"]
    search_fields = ["name", "slug", "organization__name"]
    inlines = [WorkspaceMembershipInline]
    readonly_fields = ["created", "modified"]


@admin.register(WorkspaceMembership)
class WorkspaceMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "workspace", "role", "is_active", "created"]
    list_filter = ["role", "is_active"]
    search_fields = ["user__email", "workspace__name"]
    readonly_fields = ["created", "modified"]
