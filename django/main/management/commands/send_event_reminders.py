# # Source: Generated with Claude AI, asked to create an email notification system, Apr. 28
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from main.models import EventNotificationSubscription
from clearinghouse.settings import MAILTRAP_API_TOKEN
import pytz
import mailtrap as mt

class Command(BaseCommand):
    help = 'Send email reminders for events starting in ~1 hour'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        window_start = now + timedelta(minutes=55)
        window_end = now + timedelta(minutes=75)

        # Combine date+time into a datetime for comparison
        pending = EventNotificationSubscription.objects.filter(
            notified=False
        ).select_related('user', 'event', 'event__club')

        sent_count = 0

        client = mt.MailtrapClient(token=MAILTRAP_API_TOKEN)
        for sub in pending:
            event = sub.event
            # Build a timezone-aware datetime from the event's date and time fields
            event_time_field = event.start_time or event.time
            event_dt = timezone.make_aware(
                datetime.combine(event.date, event_time_field)
            )

            if window_start <= event_dt <= window_end:
                #https://mailtrap.io/blog/django-send-email/#Send-emails-in-Django-using-email-API
                #https://devcenter.heroku.com/articles/mailtrap#local-setup
                #https://docs.mailtrap.io/developers

                mail = mt.Mail(
                        sender=mt.Address(email="events@clearinghouse.dev", name="HoosLinked"),
                        to=[mt.Address(email=sub.user.email)],
                        subject="Event Reminder",
                        text=f"Hi {sub.user.first_name or sub.user.username},\n\n"
                             f"Just a reminder that '{event.title}' hosted by {event.club.name} "
                             f"starts at {event_time_field.strftime('%I:%M %p')} today at {event.location}.\n\n"
                             f"See you there!"
                    )
                response = client.send(mail)
                sub.notified = True
                sub.save(update_fields=['notified'])
                sent_count += 1

        self.stdout.write(f"Sent {sent_count} reminder(s).")