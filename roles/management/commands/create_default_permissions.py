from django.core.management.base import BaseCommand
from roles.models import Permission

class Command(BaseCommand):
    help = 'Create default permissions for the system'

    def handle(self, *args, **options):
        # Define default permissions by module
        default_permissions = [
            # Dashboard permissions
            {
                'name': 'View Dashboard',
                'codename': 'view_dashboard',
                'description': 'Can view the main dashboard',
                'permission_type': 'read',
                'module': 'dashboard',
                'model_name': 'Dashboard',
            },
            
            # User management permissions
            {
                'name': 'View Users',
                'codename': 'view_users',
                'description': 'Can view user list and details',
                'permission_type': 'read',
                'module': 'users',
                'model_name': 'User',
            },
            {
                'name': 'Create Users',
                'codename': 'add_users',
                'description': 'Can create new users',
                'permission_type': 'create',
                'module': 'users',
                'model_name': 'User',
            },
            {
                'name': 'Edit Users',
                'codename': 'change_users',
                'description': 'Can edit user information',
                'permission_type': 'update',
                'module': 'users',
                'model_name': 'User',
            },
            {
                'name': 'Delete Users',
                'codename': 'delete_users',
                'description': 'Can delete users',
                'permission_type': 'delete',
                'module': 'users',
                'model_name': 'User',
            },
            
            # Role management permissions
            {
                'name': 'View Roles',
                'codename': 'view_roles',
                'description': 'Can view roles and permissions',
                'permission_type': 'read',
                'module': 'roles',
                'model_name': 'Role',
            },
            {
                'name': 'Create Roles',
                'codename': 'add_roles',
                'description': 'Can create new roles',
                'permission_type': 'create',
                'module': 'roles',
                'model_name': 'Role',
            },
            {
                'name': 'Edit Roles',
                'codename': 'change_roles',
                'description': 'Can edit roles and permissions',
                'permission_type': 'update',
                'module': 'roles',
                'model_name': 'Role',
            },
            {
                'name': 'Delete Roles',
                'codename': 'delete_roles',
                'description': 'Can delete roles',
                'permission_type': 'delete',
                'module': 'roles',
                'model_name': 'Role',
            },
            
            # Order management permissions
            {
                'name': 'View Orders',
                'codename': 'view_orders',
                'description': 'Can view orders',
                'permission_type': 'read',
                'module': 'orders',
                'model_name': 'Order',
            },
            {
                'name': 'Create Orders',
                'codename': 'add_orders',
                'description': 'Can create new orders',
                'permission_type': 'create',
                'module': 'orders',
                'model_name': 'Order',
            },
            {
                'name': 'Edit Orders',
                'codename': 'change_orders',
                'description': 'Can edit orders',
                'permission_type': 'update',
                'module': 'orders',
                'model_name': 'Order',
            },
            {
                'name': 'Delete Orders',
                'codename': 'delete_orders',
                'description': 'Can delete orders',
                'permission_type': 'delete',
                'module': 'orders',
                'model_name': 'Order',
            },
            
            # Inventory management permissions
            {
                'name': 'View Inventory',
                'codename': 'view_inventory',
                'description': 'Can view inventory',
                'permission_type': 'read',
                'module': 'inventory',
                'model_name': 'Product',
            },
            {
                'name': 'Manage Inventory',
                'codename': 'manage_inventory',
                'description': 'Can manage inventory levels',
                'permission_type': 'manage',
                'module': 'inventory',
                'model_name': 'Product',
            },
            
            # Seller management permissions
            {
                'name': 'View Sellers',
                'codename': 'view_sellers',
                'description': 'Can view seller information',
                'permission_type': 'read',
                'module': 'sellers',
                'model_name': 'Seller',
            },
            {
                'name': 'Manage Sellers',
                'codename': 'manage_sellers',
                'description': 'Can manage sellers and their products',
                'permission_type': 'manage',
                'module': 'sellers',
                'model_name': 'Seller',
            },
            
            # Finance permissions
            {
                'name': 'View Finance',
                'codename': 'view_finance',
                'description': 'Can view financial reports',
                'permission_type': 'read',
                'module': 'finance',
                'model_name': 'Transaction',
            },
            {
                'name': 'Manage Finance',
                'codename': 'manage_finance',
                'description': 'Can manage financial operations',
                'permission_type': 'manage',
                'module': 'finance',
                'model_name': 'Transaction',
            },
            
            # Call Center permissions
            {
                'name': 'View Call Center',
                'codename': 'view_callcenter',
                'description': 'Can view call center operations',
                'permission_type': 'read',
                'module': 'callcenter',
                'model_name': 'Call',
            },
            {
                'name': 'Manage Call Center',
                'codename': 'manage_callcenter',
                'description': 'Can manage call center operations',
                'permission_type': 'manage',
                'module': 'callcenter',
                'model_name': 'Call',
            },
            
            # Delivery permissions
            {
                'name': 'View Delivery',
                'codename': 'view_delivery',
                'description': 'Can view delivery operations',
                'permission_type': 'read',
                'module': 'delivery',
                'model_name': 'Delivery',
            },
            {
                'name': 'Manage Delivery',
                'codename': 'manage_delivery',
                'description': 'Can manage delivery operations',
                'permission_type': 'manage',
                'module': 'delivery',
                'model_name': 'Delivery',
            },
            
            # Packaging permissions
            {
                'name': 'View Packaging',
                'codename': 'view_packaging',
                'description': 'Can view packaging operations',
                'permission_type': 'read',
                'module': 'packaging',
                'model_name': 'Package',
            },
            {
                'name': 'Manage Packaging',
                'codename': 'manage_packaging',
                'description': 'Can manage packaging operations',
                'permission_type': 'manage',
                'module': 'packaging',
                'model_name': 'Package',
            },
            
            # Sourcing permissions
            {
                'name': 'View Sourcing',
                'codename': 'view_sourcing',
                'description': 'Can view sourcing operations',
                'permission_type': 'read',
                'module': 'sourcing',
                'model_name': 'SourcingRequest',
            },
            {
                'name': 'Manage Sourcing',
                'codename': 'manage_sourcing',
                'description': 'Can manage sourcing operations',
                'permission_type': 'manage',
                'module': 'sourcing',
                'model_name': 'SourcingRequest',
            },
            
            # Notifications permissions
            {
                'name': 'View Notifications',
                'codename': 'view_notifications',
                'description': 'Can view notifications',
                'permission_type': 'read',
                'module': 'notifications',
                'model_name': 'Notification',
            },
            {
                'name': 'Manage Notifications',
                'codename': 'manage_notifications',
                'description': 'Can manage notifications',
                'permission_type': 'manage',
                'module': 'notifications',
                'model_name': 'Notification',
            },
            
            # Settings permissions
            {
                'name': 'View Settings',
                'codename': 'view_settings',
                'description': 'Can view system settings',
                'permission_type': 'read',
                'module': 'settings',
                'model_name': 'Setting',
            },
            {
                'name': 'Manage Settings',
                'codename': 'manage_settings',
                'description': 'Can manage system settings',
                'permission_type': 'manage',
                'module': 'settings',
                'model_name': 'Setting',
            },
            
            # Reports permissions
            {
                'name': 'View Reports',
                'codename': 'view_reports',
                'description': 'Can view system reports',
                'permission_type': 'read',
                'module': 'reports',
                'model_name': 'Report',
            },
            {
                'name': 'Export Reports',
                'codename': 'export_reports',
                'description': 'Can export system reports',
                'permission_type': 'export',
                'module': 'reports',
                'model_name': 'Report',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for perm_data in default_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                defaults=perm_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created permission: {permission.name}')
                )
            else:
                # Update existing permission
                for key, value in perm_data.items():
                    setattr(permission, key, value)
                permission.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated permission: {permission.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(default_permissions)} permissions. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
