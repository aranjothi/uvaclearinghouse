from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_user_saved_clubs_alter_user_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='type',
            field=models.CharField(
                choices=[('message', 'Message'), ('poll', 'Poll')],
                default='message',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='announcement',
            name='allow_other',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='PollOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=300)),
                ('order', models.PositiveIntegerField(default=0)),
                ('announcement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poll_options', to='main.announcement')),
            ],
            options={'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='PollVote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('other_text', models.CharField(blank=True, max_length=500)),
                ('announcement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poll_votes', to='main.announcement')),
                ('option', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.polloption')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('announcement', 'user')}},
        ),
    ]
