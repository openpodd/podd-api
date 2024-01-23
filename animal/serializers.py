from rest_framework import serializers

from animal.models import AnimalRecord

class AnimalRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnimalRecord


class AnimalRecordUpdateSerializer(serializers.ModelSerializer):
    vaccine = serializers.WritableField("vaccine")
    last_vaccine_date = serializers.WritableField("last_vaccine_date")
    vaccine_other = serializers.WritableField("vaccine_other")
    age_month = serializers.WritableField("age_month")
    age_year = serializers.WritableField("age_year")
    birth_date = serializers.WritableField("birth_date")
    spay = serializers.WritableField("spay")
    spay_other = serializers.WritableField("spay_other")
    updated_by = serializers.WritableField("updated_by")
    raising = serializers.WritableField("raising")
    raising_place = serializers.WritableField("raising_place")

    class Meta:
        model = AnimalRecord
        fields = ["vaccine", "last_vaccine_date", "vaccine_other",  "age_month", "age_year", "birth_date", "spay", "spay_other", "updated_by"]


class AnimalRecordDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnimalRecord
        fields = ["deleted_by", "deleted_date", "updated_by"]


class AnimalRecordMarkDeathSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnimalRecord
        fields = ["death_updated_by", "death_updated_date", "updated_by"]
