from django import forms
from group import models


class ScheduledMessagesForm(forms.ModelForm):
    interval = forms.DurationField(help_text='[DD] [[hh:]mm:]ss')

    class Meta:
        model = models.ScheduledMessages
        fields = '__all__'
