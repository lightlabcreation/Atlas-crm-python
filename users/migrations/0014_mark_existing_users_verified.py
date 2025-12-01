# Mark all existing users as email verified

from django.db import migrations


def mark_existing_users_verified(apps, schema_editor):
    User = apps.get_model('users', 'User')
    # Mark all existing users as email verified
    User.objects.all().update(email_verified=True)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_user_email_verification'),
    ]

    operations = [
        migrations.RunPython(mark_existing_users_verified),
    ]

