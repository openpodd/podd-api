# -*- encoding: utf-8 -*-
import json

from rest_framework import serializers
from django.template import Template, Context

from taggit.models import Tag


class TagSerializer(serializers.ModelSerializer):
    # text = serializers.WritableField('name', read_only=True)

    class Meta:
        model = Tag
        fields = ('name', )
