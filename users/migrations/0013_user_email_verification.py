# Generated manually for email verification fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_alter_user_first_name_alter_user_last_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False, verbose_name='email verified'),
        ),
        migrations.AddField(
            model_name='user',
            name='verification_code',
            field=models.CharField(blank=True, max_length=6, null=True, verbose_name='verification code'),
        ),
        migrations.AddField(
            model_name='user',
            name='verification_code_sent_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='verification code sent at'),
        ),
        migrations.AddField(
            model_name='user',
            name='verification_code_expires_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='verification code expires at'),
        ),
    ]