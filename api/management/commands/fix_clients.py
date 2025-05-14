from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Client, UserProfile
from django.db import transaction

class Command(BaseCommand):
    help = 'Fixes clients with missing user associations by creating new users for them'

    def handle(self, *args, **options):
        # Find clients without users
        clients_without_users = Client.objects.filter(user__isnull=True)
        self.stdout.write(f"Found {clients_without_users.count()} clients without users")
        
        # Create users for each client
        for client in clients_without_users:
            try:
                with transaction.atomic():
                    # Create a new user based on the client company name
                    username = client.company_name.lower().replace(' ', '_')[:30]
                    # Add number suffix if username exists
                    suffix = 1
                    original_username = username
                    while User.objects.filter(username=username).exists():
                        username = f"{original_username[:27]}_{suffix}"
                        suffix += 1
                    
                    # Create the user
                    user = User.objects.create_user(
                        username=username,
                        email=client.contact_email or '',
                        password=User.objects.make_random_password()
                    )
                    
                    # Set names if available
                    if client.contact_person:
                        parts = client.contact_person.split(' ', 1)
                        user.first_name = parts[0]
                        if len(parts) > 1:
                            user.last_name = parts[1]
                        user.save()
                    
                    # Ensure the user has a profile
                    if not hasattr(user, 'profile'):
                        UserProfile.objects.create(user=user, role='CLIENT')
                    else:
                        user.profile.role = 'CLIENT'
                        user.profile.save()
                    
                    # Associate the client with the user
                    client.user = user
                    client.save()
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"Created user {username} for client {client.company_name}"
                    ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error processing client {client.company_name}: {str(e)}"
                ))
        
        self.stdout.write(self.style.SUCCESS("Completed fixing clients without users")) 