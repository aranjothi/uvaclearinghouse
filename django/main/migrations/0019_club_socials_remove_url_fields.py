from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0018_club_tags_socials'),
    ]

    operations = [
        migrations.RemoveField(model_name='club', name='instagram_url'),
        migrations.RemoveField(model_name='club', name='twitter_url'),
        migrations.RemoveField(model_name='club', name='linkedin_url'),
        migrations.RemoveField(model_name='club', name='website_url'),
        migrations.AddField(
            model_name='club',
            name='socials',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
