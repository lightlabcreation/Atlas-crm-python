# Generated manually on 2025-01-15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0018_order_escalated_at_order_escalated_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='escalation_reason',
            field=models.TextField(blank=True, help_text='Reason for escalating to manager', verbose_name='Escalation Reason'),
        ),
    ]
