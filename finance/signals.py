"""
Finance module signals for automatic OrderFee creation and order-finance integration.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal


@receiver(post_save, sender='orders.Order')
def create_order_fee(sender, instance, created, **kwargs):
    """
    Automatically create OrderFee when a new Order is created.
    This ensures every order has associated fee tracking from the start.
    """
    if created:
        from .models import OrderFee, SellerFee

        # Check if OrderFee already exists (shouldn't but just in case)
        if not hasattr(instance, 'order_fees') or not OrderFee.objects.filter(order=instance).exists():
            # Calculate base price using Decimal
            price = Decimal(str(instance.price_per_unit or 0))
            qty = Decimal(str(instance.quantity or 1))
            base_price = price * qty

            # Get seller fee if seller exists
            seller_fee_amount = Decimal('0.00')
            if instance.seller:
                seller_fee_obj = SellerFee.objects.filter(seller=instance.seller, is_active=True).first()
                if seller_fee_obj:
                    seller_fee_amount = base_price * (Decimal(str(seller_fee_obj.fee_percentage)) / Decimal('100'))
            elif instance.product and instance.product.seller:
                seller_fee_obj = SellerFee.objects.filter(seller=instance.product.seller, is_active=True).first()
                if seller_fee_obj:
                    seller_fee_amount = base_price * (Decimal(str(seller_fee_obj.fee_percentage)) / Decimal('100'))

            # Create OrderFee with calculated values using Decimal arithmetic
            OrderFee.objects.create(
                order=instance,
                seller_fee=seller_fee_amount,
                upsell_fee=base_price * Decimal('0.03'),  # 3% of order value
                confirmation_fee=Decimal('10.00'),  # Fixed fee
                fulfillment_fee=base_price * Decimal('0.02'),  # 2% of order value
                shipping_fee=Decimal('12.00'),  # Fixed shipping fee
                warehouse_fee=base_price * Decimal('0.01'),  # 1% warehouse fee
                tax_rate=Decimal('5.00'),  # 5% VAT
            )


@receiver(post_save, sender='orders.Order')
def update_order_fee_on_status_change(sender, instance, created, **kwargs):
    """
    Update OrderFee when order status changes (e.g., add cancellation fee).
    """
    if not created:
        from .models import OrderFee

        try:
            order_fee = OrderFee.objects.get(order=instance)

            # Add cancellation fee if order is cancelled
            if instance.status == 'cancelled' and order_fee.cancellation_fee == 0:
                order_fee.cancellation_fee = Decimal('5.00')
                order_fee.save()

            # Add return fee if order is returned
            if instance.status == 'returned' and order_fee.return_fee == 0:
                order_fee.return_fee = Decimal('15.00')
                order_fee.save()

        except OrderFee.DoesNotExist:
            # Create OrderFee if it doesn't exist for existing orders
            price = Decimal(str(instance.price_per_unit or 0))
            qty = Decimal(str(instance.quantity or 1))
            base_price = price * qty
            
            OrderFee.objects.create(
                order=instance,
                upsell_fee=base_price * Decimal('0.03'),
                confirmation_fee=Decimal('10.00'),
                fulfillment_fee=base_price * Decimal('0.02'),
                shipping_fee=Decimal('12.00'),
                warehouse_fee=base_price * Decimal('0.01'),
                cancellation_fee=Decimal('5.00') if instance.status == 'cancelled' else Decimal('0.00'),
                return_fee=Decimal('15.00') if instance.status == 'returned' else Decimal('0.00'),
                tax_rate=Decimal('5.00'),
            )
