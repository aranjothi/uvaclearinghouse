from django import forms
from .models import Event


class EventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "date",
            "end_date",
            "time",
            "start_time",
            "end_time",
            "location",
            "category",
            "image",
        ]