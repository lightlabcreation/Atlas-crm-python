from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from roles.models import Role, Permission, RolePermission

User = get_user_model()

class Command(BaseCommand):
    help = 'Create default roles for the system'

    def handle(self, *args, **options):
        # Define default roles
        default_roles = [
            {
                'name': 'Super Admin',
                'role_type': 'admin',
                'description': 'Full system access with all permissions',
                'is_active': True,
                'is_default': True,
                'is_protected': True,
            },
            {
                'name': 'Admin',
                'role_type': 'admin',
                'description': 'Administrative access to most system features',
                'is_active': True,
                'is_default': True,
                'is_protected': True,
            },
            {
                'name': 'Delivery Manager',
                'role_type': 'manager',
                'description': 'Manages delivery operations, agents, and assignments',
                'is_active': True,
                'is_default': False,
                'is_protected': True,
            },
            {
                'name': 'Call Center Agent',
                'role_type': 'operator',
                'description': 'Call center operations and customer service',
                'is_active': True,
                'is_default': True,
                'is_protected': True,
            },
            {
                'name': 'Call Center Manager',
                'role_type': 'manager',
                'description': 'Call center management and supervision',
                'is_active': True,
                'is_default': True,
                'is_protected': True,
            },
            {
                'name': 'Seller',
                'role_type': 'specialist',
                'description': 'Seller account with product management access',
                'is_active': True,
                'is_default': True,
                'is_protected': True,
            },
            {
                'name': 'Accountant',
                'role_type': 'specialist',
                'description': 'Financial management and reporting access',
                'is_active': True,
                'is_default': True,
                'is_protected': True,
            },
            {
                'name': 'Stock Keeper',
                'role_type': 'specialist',
                'description': 'Inventory and warehouse management',
                'is_active': True,
                'is_default': True,
                'is_protected': True,
            },
            {
                'name': 'Viewer',
                'role_type': 'viewer',
                'description': 'Read-only access to assigned modules',
                'is_active': True,
                'is_default': True,
                'is_protected': False,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for role_data in default_roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults=role_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created role: {role.name}')
                )
            else:
                # Update existing role
                for key, value in role_data.items():
                    setattr(role, key, value)
                role.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated role: {role.name}')
                )
        
        # Assign permissions to roles
        self.assign_permissions_to_roles()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(default_roles)} roles. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )

    def assign_permissions_to_roles(self):
        """Assign appropriate permissions to each role"""
        
        # Get all permissions
        all_permissions = Permission.objects.all()
        
        # Define role-permission mappings
        role_permissions = {
            'Super Admin': [perm.codename for perm in all_permissions],
            'Admin': [
                'view_dashboard', 'view_users', 'add_users', 'change_users',
                'view_roles', 'view_orders', 'add_orders', 'change_orders',
                'view_inventory', 'manage_inventory', 'view_sellers', 'manage_sellers',
                'view_finance', 'manage_finance', 'view_callcenter', 'manage_callcenter'
            ],
            'Delivery Manager': [
                'view_dashboard',
                'view_orders', 'change_orders',
                'view_delivery', 'manage_delivery',
            ],
            'Call Center Manager': [
                'view_dashboard', 'view_orders', 'add_orders', 'change_orders',
                'view_inventory', 'view_sellers', 'view_callcenter', 'manage_callcenter'
            ],
            'Call Center Agent': [
                'view_dashboard', 'view_orders', 'add_orders', 'change_orders',
                'view_inventory', 'view_sellers', 'view_callcenter'
            ],
            'Seller': [
                'view_dashboard', 'view_inventory', 'manage_inventory', 'view_sellers',
                'view_orders', 'add_orders', 'change_orders'
            ],
            'Accountant': [
                'view_dashboard', 'view_finance', 'manage_finance', 'view_orders',
                'view_sellers', 'view_inventory'
            ],
            'Stock Keeper': [
                'view_dashboard', 'view_inventory', 'manage_inventory', 'view_orders',
                'view_sellers'
            ],
            'Viewer': [
                'view_dashboard', 'view_orders', 'view_inventory', 'view_sellers',
                'view_finance', 'view_callcenter'
            ],
        }
        
        for role_name, permission_codenames in role_permissions.items():
            try:
                role = Role.objects.get(name=role_name)
                
                # Clear existing permissions
                role.role_permissions.all().delete()
                
                # Add new permissions
                for codename in permission_codenames:
                    try:
                        permission = Permission.objects.get(codename=codename)
                        RolePermission.objects.create(
                            role=role,
                            permission=permission,
                            granted=True
                        )
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'Permission {codename} not found, skipping...')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Assigned {len(permission_codenames)} permissions to {role_name}')
                )
                
            except Role.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Role {role_name} not found, skipping permission assignment...')
                )
