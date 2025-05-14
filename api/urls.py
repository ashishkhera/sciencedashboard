from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, ProjectViewSet, CommentViewSet, ProjectLinkViewSet, LoginView, ResourceViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'links', ProjectLinkViewSet)
router.register(r'resources', ResourceViewSet)

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    # Authentication URLs
    path('auth/login/', LoginView.as_view(), name='login'),
    # Add other URL patterns here if needed
] 