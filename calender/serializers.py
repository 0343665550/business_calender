from rest_framework import serializers

from .models import ExpectedCalender


class ExpectedSerialize(serializers.ModelSerializer):

    class Meta:
        model = ExpectedCalender
        fields = ('week', 'content', 'create_uid', 'create_date', )