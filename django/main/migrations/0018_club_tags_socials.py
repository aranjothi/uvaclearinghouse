from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_announcement_type_polloption_pollvote'),
    ]

    operations = [
        migrations.AddField(
            model_name='club',
            name='tags',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='club',
            name='instagram_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='club',
            name='twitter_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='club',
            name='linkedin_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='club',
            name='website_url',
            field=models.URLField(blank=True),
        ),
    ]
