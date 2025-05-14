from django.contrib import admin
from .models import UserProfile, Client, Project, Comment, ProjectLink

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'client_type', 'contact_person', 'contact_email', 'created_at')
    list_filter = ('client_type', 'created_at',)
    search_fields = ('company_name', 'contact_person', 'contact_email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('company_name', 'user', 'client_type')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_email')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Define inlines first before using them
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    readonly_fields = ('created_at',)


class ProjectLinkInline(admin.TabularInline):
    model = ProjectLink
    extra = 1
    readonly_fields = ('created_at',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_number', 'client', 'description', 'status', 
                   'client_delivery_date', 'internal_due_date', 'assigned_resource', 'updated_at')
    list_filter = ('status', 'client', 'assigned_resource', 'client_delivery_date', 'internal_due_date')
    search_fields = ('project_number', 'description', 'client__company_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CommentInline, ProjectLinkInline]
    fieldsets = (
        (None, {
            'fields': ('project_number', 'client', 'description')
        }),
        ('Status & Dates', {
            'fields': ('status', 'client_delivery_date', 'internal_due_date')
        }),
        ('Assignment', {
            'fields': ('assigned_resource',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'text', 'created_at')
    list_filter = ('created_at', 'user', 'project')
    search_fields = ('text', 'project__description', 'user__username')
    readonly_fields = ('created_at',)


@admin.register(ProjectLink)
class ProjectLinkAdmin(admin.ModelAdmin):
    list_display = ('project', 'description', 'url', 'added_by', 'created_at')
    list_filter = ('created_at', 'added_by', 'project')
    search_fields = ('description', 'url', 'project__description')
    readonly_fields = ('created_at',)
