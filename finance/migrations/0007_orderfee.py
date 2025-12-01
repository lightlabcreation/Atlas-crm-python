# Generated manually for OrderFee model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0006_add_payment_platforms'),
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderFee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seller_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('upsell_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('confirmation_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('cancellation_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('fulfillment_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('shipping_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('return_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('warehouse_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('total_fees', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('tax_rate', models.DecimalField(decimal_places=2, default=5.0, max_digits=5)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('final_total', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('notes', models.TextField(blank=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='order_fees', to='orders.order')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_fees', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Order Fee',
                'verbose_name_plural': 'Order Fees',
                'ordering': ['-updated_at'],
            },
        ),
    ]

