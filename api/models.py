from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class UserProfile(models.Model):
    """
    Extends the built-in Django User model with additional fields.
    """
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('CLIENT', 'Client'),
        ('RESOURCE', 'Resource'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CLIENT')
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class Client(models.Model):
    """
    Represents a client company.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile', 
                              limit_choices_to={'profile__role': 'CLIENT'})
    company_name = models.CharField(max_length=255, unique=True)
    contact_person = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    CLIENT_TYPE_CHOICES = (
        ('INTERNAL', 'Internal'),
        ('EXTERNAL', 'External'),
    )
    client_type = models.CharField(
        max_length=10,
        choices=CLIENT_TYPE_CHOICES,
        default='EXTERNAL',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.company_name


class Resource(models.Model):
    """
    Represents a resource/team member who can be assigned to projects.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resource_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    title = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Project(models.Model):
    """
    Represents a project for a client.
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('IN_QUEUE', 'In Queue'),
        ('FOR_REVIEW', 'For Review'),
        ('CONCEPTUAL', 'Conceptual'),
        ('COMPLETE', 'Complete'),
        ('PAUSED', 'Paused'),
    )
    
    project_number = models.CharField(max_length=50, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_QUEUE')
    client_delivery_date = models.DateField(null=True, blank=True)
    internal_due_date = models.DateField(null=True, blank=True)
    # Keep for backward compatibility but mark as deprecated
    assigned_resource = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_projects',
        limit_choices_to={'profile__role': 'ADMIN'},
        help_text="Deprecated: Use resources instead"
    )
    # New field for multiple resources
    resources = models.ManyToManyField(
        Resource,
        related_name='projects',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.project_number or 'No ID'} - {self.client.company_name}"


class Comment(models.Model):
    """
    Represents a comment on a project.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username if self.user else 'Unknown'} on {self.project}"


class ProjectLink(models.Model):
    """
    Represents a URL link associated with a project.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='links')
    url = models.URLField()
    description = models.CharField(max_length=255, blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='added_links')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.description or self.url} for {self.project}"

# Signal to create a UserProfile when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()
