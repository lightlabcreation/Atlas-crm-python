"""
Audit logging configuration for critical models.
Register models that need audit trails as per spec requirements.
"""
from auditlog.registry import auditlog


def register_audit_models():
    """
    Register critical models for audit logging.
    Per spec: Role/Permission changes, Manual inventory adjustments, Credit balance modifications
    """
    try:
        # Import models
        from roles.models import Role, Permission
        from inventory.models import Stock, InventoryMovement
        from finance.models import Payment, Invoice
        from sellers.models import SellerProfile
        from users.models import User
        from sourcing.models import SourcingRequest
        from orders.models import Order, Return

        # Register for audit logging
        auditlog.register(Role)
        auditlog.register(Permission)
        auditlog.register(Stock)
        auditlog.register(InventoryMovement)
        auditlog.register(Payment)
        auditlog.register(Invoice)
        auditlog.register(SellerProfile)
        auditlog.register(User)
        auditlog.register(SourcingRequest)
        auditlog.register(Order)
        auditlog.register(Return)

        print("✅ Audit logging configured for critical models")
    except Exception as e:
        print(f"⚠️ Could not register all models for audit logging: {e}")
