from django.db import migrations

def remove_sourcing_followup_roles(apps, schema_editor):
    """Remove Sourcing Agent and Follow-up Agent roles from the system."""
    Role = apps.get_model('roles', 'Role')
    UserRole = apps.get_model('roles', 'UserRole')
    
    # Remove user roles first
    UserRole.objects.filter(role__name__in=['Sourcing Agent', 'Follow-up Agent']).delete()
    
    # Remove the roles
    Role.objects.filter(name__in=['Sourcing Agent', 'Follow-up Agent']).delete()
    
    print("Removed Sourcing Agent and Follow-up Agent roles from the system.")

def reverse_remove_sourcing_followup_roles(apps, schema_editor):
    """Reverse the removal of Sourcing Agent and Follow-up Agent roles."""
    Role = apps.get_model('roles', 'Role')
    
    # Recreate the roles
    Role.objects.get_or_create(
        name='Sourcing Agent',
        defaults={
            'description': 'Handles product sourcing and supplier management',
            'is_protected': True,
            'is_default': False,
        }
    )
    
    Role.objects.get_or_create(
        name='Follow-up Agent',
        defaults={
            'description': 'Handles customer follow-up and support',
            'is_protected': True,
            'is_default': False,
        }
    )
    
    print("Recreated Sourcing Agent and Follow-up Agent roles.")

class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0002_build_in_roles'),
    ]

    operations = [
        migrations.RunPython(remove_sourcing_followup_roles, reverse_remove_sourcing_followup_roles),
    ]
