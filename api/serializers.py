from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Client, Project, Comment, ProjectLink, Resource
from django.db import transaction
import secrets
import string


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['username', 'email']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role']


class ClientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Client
        fields = ['id', 'user', 'company_name', 'contact_person', 'contact_email', 'client_type', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        # Get the current user from the request context
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # Create a new user for this client
            with transaction.atomic():
                # Generate username from company name
                username = validated_data['company_name'].lower().replace(' ', '_')[:30]
                suffix = 1
                original_username = username
                
                # Ensure username is unique
                while User.objects.filter(username=username).exists():
                    username = f"{original_username[:27]}_{suffix}"
                    suffix += 1
                
                # Generate a random password
                alphabet = string.ascii_letters + string.digits
                password = ''.join(secrets.choice(alphabet) for i in range(12))
                
                # Create new user
                new_user = User.objects.create_user(
                    username=username,
                    email=validated_data.get('contact_email', ''),
                    password=password
                )
                
                # Set user profile to CLIENT role
                if not hasattr(new_user, 'profile'):
                    UserProfile.objects.create(user=new_user, role='CLIENT')
                else:
                    new_user.profile.role = 'CLIENT'
                    new_user.profile.save()
                
                # Create client with new user
                validated_data['user'] = new_user
                return super().create(validated_data)
        else:
            raise serializers.ValidationError("Unable to create client: no authenticated user found")


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'project', 'text', 'created_at']
        read_only_fields = ['created_at']


class ProjectLinkSerializer(serializers.ModelSerializer):
    added_by = UserSerializer(read_only=True)

    class Meta:
        model = ProjectLink
        fields = ['id', 'project', 'url', 'description', 'added_by', 'created_at']
        read_only_fields = ['created_at']


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['id', 'first_name', 'last_name', 'email', 'title', 'is_active', 'created_at', 'updated_at', 'full_name']
        read_only_fields = ['created_at', 'updated_at', 'full_name']
    
    def create(self, validated_data):
        # Create a user for this resource if not provided
        user_data = self.context.get('user', None)
        
        with transaction.atomic():
            if not user_data:
                # Generate a username from first_name and last_name
                first_name = validated_data.get('first_name', '')
                last_name = validated_data.get('last_name', '')
                username = f"{first_name.lower()}_{last_name.lower()}"[:30]
                
                # Ensure username is unique
                suffix = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username[:27]}_{suffix}"
                    suffix += 1
                
                # Generate a random password
                alphabet = string.ascii_letters + string.digits
                password = ''.join(secrets.choice(alphabet) for i in range(12))
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=validated_data.get('email', ''),
                    password=password,
                    first_name=validated_data.get('first_name', ''),
                    last_name=validated_data.get('last_name', '')
                )
                
                # Set user profile to RESOURCE role
                user.profile.role = 'RESOURCE'
                user.profile.save()
            else:
                user = user_data
            
            # Create resource with the user
            resource = Resource.objects.create(user=user, **validated_data)
            return resource


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating projects with proper client handling
    """
    resources = serializers.PrimaryKeyRelatedField(
        queryset=Resource.objects.filter(is_active=True),
        many=True,
        required=False
    )
    
    class Meta:
        model = Project
        fields = [
            'id', 'project_number', 'client', 'description', 
            'status', 'client_delivery_date', 'internal_due_date', 
            'assigned_resource', 'resources',
        ]

    def to_representation(self, instance):
        # Return the detail representation after create/update
        detail_serializer = ProjectDetailSerializer(instance, context=self.context)
        return detail_serializer.data


class ProjectDetailSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    assigned_resource = UserSerializer(read_only=True)
    resources = ResourceSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    links = ProjectLinkSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'project_number', 'client', 'description', 
            'status', 'client_delivery_date', 'internal_due_date', 
            'assigned_resource', 'resources', 'created_at', 'updated_at',
            'comments', 'links'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProjectListSerializer(serializers.ModelSerializer):
    client_name = serializers.ReadOnlyField(source='client.company_name')
    assigned_resource_name = serializers.SerializerMethodField()
    resources_list = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'project_number', 'client', 'client_name', 'description', 
            'status', 'client_delivery_date', 'internal_due_date', 
            'assigned_resource', 'assigned_resource_name', 'resources', 'resources_list', 'updated_at'
        ]
    
    def get_assigned_resource_name(self, obj):
        if obj.assigned_resource:
            return f"{obj.assigned_resource.first_name} {obj.assigned_resource.last_name}".strip() or obj.assigned_resource.username
        return None
    
    def get_resources_list(self, obj):
        return [{'id': r.id, 'name': r.full_name} for r in obj.resources.all()] 