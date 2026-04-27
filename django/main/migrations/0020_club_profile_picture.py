from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_club_socials_remove_url_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='club',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='club_profile_pics/'),
        ),
    ]
