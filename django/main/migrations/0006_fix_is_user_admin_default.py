from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_user_is_user_admin_alter_club_executive_code'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE main_user ALTER COLUMN is_user_admin SET DEFAULT false;",
            reverse_sql="ALTER TABLE main_user ALTER COLUMN is_user_admin DROP DEFAULT;",
        ),
    ]
