from rest_framework import serializers
from indicator import models as indicator_models
from geodata import models as geo_models
from file_upload.models import File, FileTag
from api.generics.serializers import DynamicFieldsModelSerializer


class IndicatorCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = indicator_models.IndicatorCategory
        fields = (
            'id',
            'code')


class RegionSerializer(serializers.ModelSerializer):

    class Meta:
        model = geo_models.Region
        fields = (
            'code',
            'name')


class CountrySerializer(serializers.ModelSerializer):

    region = RegionSerializer()
    
    class Meta:
        model = geo_models.Country
        fields = (
            'code',
            'name',
            'region')


class FileTagSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FileTag
        fields = ('file_id','name')
        #fields = (
        #    #'file_id',Kieran: this should work but doesn't removing for deployment
        #    'name')


class FileSerializer(serializers.ModelSerializer):
    file_tags = FileTagSerializer(source="tags", many=True, read_only=True)
    
    class Meta:
        model = File
        fields = (
            'id',
            'file_name',
            'created',
            'file_tags')


class IndicatorCategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = indicator_models.IndicatorCategory
        fields = (
            'id',
            'code',
            'indicator') 


class IndicatorSerializer(serializers.ModelSerializer):

    country = CountrySerializer()
    file = FileSerializer()
    indicator_category = IndicatorCategorySerializer()


    class Meta:
        model = indicator_models.IndicatorDatapoint
        fields = (
            'id',
            'file',
            'date_format',
            'indicator_category',
            'indicator',
            'country',
            'date_value',
            'source',
            "measure_value",
            "unit_of_measure",
            'other')
