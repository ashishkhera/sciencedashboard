print('api/views.py loaded')
from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from .models import UserProfile, Client, Project, Comment, ProjectLink, Resource
from .serializers import (
    UserSerializer, UserProfileSerializer, ClientSerializer,
    ProjectListSerializer, ProjectDetailSerializer, ProjectCreateUpdateSerializer,
    CommentSerializer, ProjectLinkSerializer, ResourceSerializer
)

# Custom permission classes
class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'


class IsClientUser(permissions.BasePermission):
    """
    Allows access only to client users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'CLIENT'


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows full access to admin users, but only read-only access to clients.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return request.user.is_authenticated
        return request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'


class ClientViewSet(viewsets.ModelViewSet):
    """
    API endpoint for clients.
    Admins can view and edit, clients have no access.
    """
    queryset = Client.objects.all().order_by('company_name')
    serializer_class = ClientSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['company_name', 'contact_person', 'contact_email']
    filterset_fields = ['company_name']
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for projects.
    Admins can view and edit all projects.
    Clients can only view their own projects.
    """
    queryset = Project.objects.all().order_by('-updated_at')
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['project_number', 'description']
    filterset_fields = ['status', 'client', 'assigned_resource']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProjectCreateUpdateSerializer
        return ProjectListSerializer

    def get_queryset(self):
        """
        Filter projects based on user role:
        - Admins see all projects
        - Clients see only their own projects
        """
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'ADMIN':
            return Project.objects.all().order_by('-updated_at')
        if hasattr(user, 'client_profile'):
            return Project.objects.filter(client=user.client_profile).order_by('-updated_at')
        return Project.objects.none()


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for comments.
    Admins can view and edit all comments.
    Clients can only view comments on their own projects.
    """
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project']

    def get_queryset(self):
        """
        Filter comments based on user role:
        - Admins see all comments
        - Clients see only comments on their own projects
        """
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'ADMIN':
            return Comment.objects.all().order_by('-created_at')
        if hasattr(user, 'client_profile'):
            return Comment.objects.filter(project__client=user.client_profile).order_by('-created_at')
        return Comment.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProjectLinkViewSet(viewsets.ModelViewSet):
    """
    API endpoint for project links.
    Admins can view and edit all links.
    Clients can only view links on their own projects.
    """
    queryset = ProjectLink.objects.all().order_by('-created_at')
    serializer_class = ProjectLinkSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project']

    def get_queryset(self):
        """
        Filter links based on user role:
        - Admins see all links
        - Clients see only links on their own projects
        """
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'ADMIN':
            return ProjectLink.objects.all().order_by('-created_at')
        if hasattr(user, 'client_profile'):
            return ProjectLink.objects.filter(project__client=user.client_profile).order_by('-created_at')
        return ProjectLink.objects.none()

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)


class ResourceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for resources.
    Admins can view and edit, clients have no access.
    """
    queryset = Resource.objects.all().order_by('first_name', 'last_name')
    serializer_class = ResourceSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['first_name', 'last_name', 'email', 'title']
    filterset_fields = ['is_active']

# Authentication views
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny

class LoginView(APIView):
    """
    API endpoint for user login
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        print(f"Content-Type: {request.content_type}")
        print(f"Request data: {request.data}")
        username = request.data.get('username')
        password = request.data.get('password')
        print(f"Login attempt: username={username}, password={'*' * len(password) if password else None}")
        user = authenticate(username=username, password=password)
        print(f"Authentication result: user={user}")
        if user:
            try:
                profile = user.profile
                print(f"User profile: role={profile.role}")
                # Create or get token
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    },
                    'profile': {
                        'id': profile.id,
                        'role': profile.role
                    }
                })
            except UserProfile.DoesNotExist:
                print("UserProfile does not exist for this user")
                return Response(
                    {'error': 'User profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
