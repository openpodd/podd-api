from rest_framework import serializers

from civic.models import LetterFieldConfiguration


class LetterFieldConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterFieldConfiguration
        fields = (
            'id',
            'code',
            'header_address1',
            'header_address2',
            'sign_name',
            'sign_position1',
            'sign_position2',
            'footer_contact_line1',
            'footer_contact_line2',
            'footer_contact_line3',
        )
