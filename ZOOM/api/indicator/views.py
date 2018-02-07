from django.db.models import Count, Sum, F, Avg, Max, Min
from django.db.models import FloatField
from django.db.models.functions import Cast
from rest_framework.filters import DjangoFilterBackend
from rest_framework.generics import RetrieveAPIView, GenericAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from file_upload.models import File, FileSource
from indicator.models import IndicatorDatapoint, Indicator, update_indicator_counts, IndicatorFilter, IndicatorFilterHeading
from geodata.models import Country
from api.indicator.serializers import IndicatorSerializer, IndicatorDataSerializer, IndicatorFilterSerializer
from api.indicator.filters import IndicatorFilters, IndicatorDataFilter, SearchFilter, IndicatorFilterFilters
from api.aggregation.views import AggregationView, Aggregation, GroupBy
from api.generics.views import DynamicListView

from rest_framework import serializers

#Better solution needed here!
@api_view(['GET'])#should do this using ListAPIView as it already does this but don't have time now
def show_unique_filters(request):
    if(not 'dataType' in request.GET):
        return Response({"success":0, "results":"Need data type"})
    
    data_source = request.GET['dataType']
    
    if("heading" in request.GET):
        heading = request.GET['heading']
        queryset = IndicatorFilter.objects.filter(file_source = FileSource.objects.get(name=data_source), heading = IndicatorFilterHeading.objects.get(name=heading))
    else:
        queryset = IndicatorFilter.objects.all()

    if("filters" in request.GET):
        data_filter = IndicatorDatapoint.objects.all()
        applied_filters = request.GET['filters'].split(",")
        filter_set = IndicatorFilter.objects.all()
        
        for i in applied_filters:
            filter_set = filter_set.filter(name=i)
            filter_set = data_filter.filter(id__in=filter_set.values_list('measure_value'))
            #need to do this to ensure other filters are not filtered out 
            queryset = queryset.filter(measure_value__in=filter_set.values_list('id'))
        
    if("indicator" in request.GET):
        ind_filter = Indicator.objects.filter(id=request.GET['indicator'])
        queryset = queryset.filter(measure_value__in=ind_filter.set.value_list("id"))


    if('country__name' in request.GET):
        country_filter = Country.objects.get(name=request.GET['country__name'])
        ind_filter = Indicator,objects.filter(country=country_filter)
        queryset = queryset.filter(measure_value__in=ind_filter.set.value_list("id"))

    queryset = queryset.values('name').annotate(count=Count('name'))    #implement sort here
    overall_count = queryset.count()
    
    if('order_by' in request.GET):
        queryset = queryset.order_by(request.GET['order_by'])
    
    if('page_size' in request.GET and not request.GET['page_size'] == "all"):
        page_size = int(request.GET['page_size'])
        if('page' in request.GET and page_size > 0 ):
            queryset = queryset[(page_size * int(request.GET['page']) - page_size): (page_size * int(request.GET['page']))]
        else:
            queryset = queryset[0:page_size]

    return Response({"success":1, "count": overall_count, "results": list(queryset)})


@api_view(['GET'])
def get_filter_headings(request):
    if(not request.GET['dataType']):
        return Response({"success":0, "results":IndicatorFilter.objects.all()})
    
    data_source = request.GET['dataType']
    x = IndicatorFilter.objects.filter(file_source = FileSource.objects.get(name="CRS")).values_list("heading")
    x = [x[0] for x in list(set(x.values_list("heading")))] 
    return Response({"success":1, "results": x})


@api_view(['POST'])
def reset_mapping(request):
    file = File.objects.get(id=request.data['file_id'])
    indicators = IndicatorDatapoint.objects.filter(file=file)
    #foreign keys 
    indicators.delete()
    update_indicator_counts()
    return Response({"success":1})

class IndicatorFilterList(ListAPIView):
    queryset = IndicatorFilter.objects.all()
    
    filter_backends = (DjangoFilterBackend, )
    #override method in 
    filter_class = IndicatorFilterFilters
    serializer_class = IndicatorFilterSerializer

    fields = (
        'name',
        'heading',
        'measure_value',
        'file_source'
    )

    #temp
    """def filter_queryset(self, request, queryset, view):
        queryset = super(self, IndicatorFilterList).filter_queryset(self, request, queryset, view)
        ##
        #get ?sector

        return queryset"""

class IndicatorList(ListAPIView):
    queryset = Indicator.objects.all().distinct() #.values("indicator").distinct() #Indicator.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filter_class = IndicatorFilters
    serializer_class = IndicatorSerializer
    #ordering = get_ordering

    '''def get_ordering(self):
        ordering = self.GET.get('ordering', '-indicator')
        # validate ordering here
        return ordering'''

    fields = (
        'id',
        'description',
        'count',
        'file_source'
    )


def check_filters(instance):
    queryset = instance.queryset
    request = instance.request.query_params.get('filters') 
    
    if request:
        applied_filters = request.split(",")
        filter_set = IndicatorFilter.objects.all()
        for i in applied_filters:
            filter_set = filter_set.filter(name=i)
        queryset = queryset.filter(id__in=filter_set.values_list('measure_value'))
    return queryset


class IndicatorDataList(ListAPIView):

    queryset = IndicatorDatapoint.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filter_class = IndicatorDataFilter
    serializer_class = IndicatorDataSerializer

    def get_queryset(self):
        #filter according to filter tag
        return check_filters(self)

    fields = (
        'id',
        'file',
        'date_format',
        #'indicator_category',
        'indicator',
        'country',
        'date_value',
        'source',
        'measure_value',
        'unit_of_measure',
        'other'
    )

    # def get_queryset(self):
    #     if self.request.data.get('group_by') is None:
    #         return IndicatorDatapoint.objects.none()
    #     return IndicatorDatapoint.objects.all()

'''
Data Post Example:

# Without date_value filter:

{
            "indicator_x" : "Bananas",
            "indicator_category_x" : "Area Harvested",
            "indicator_y" : "Pigs",
            "indicator_category_y": "Stocks"
}

# With date_value filter:

{
            "indicator_x" : "Bananas",
            "indicator_category_x" : "Area Harvested",
            "indicator_y" : "Pigs",
            "indicator_category_y": "Stocks",
            "date_value": "2004"
}
'''

"""class IndicatorCategoryDataList(ListAPIView):

    queryset = IndicatorCategory.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filter_class = IndicatorCategoryDataFilter
    serializer_class = IndicatorCategorySerializer

    fields = (
        'id',
        'unique_identifier',
        'name',
        'level',
        'child',
        'indicator',
    )"""


def annotate_measure(query_params, groupings):

    annotation_components = F('measure_value')

    return Sum(Cast(annotation_components, FloatField()))

def mean_measure(query_params, groupings):

    annotation_components = F('measure_value')

    return Avg(Cast(annotation_components, FloatField()))

def max_measure(query_params, groupings):

    annotation_components = F('measure_value')

    return Max(Cast(annotation_components, FloatField()))

def min_measure(query_params, groupings):

    annotation_components = F('measure_value')

    return Min(Cast(annotation_components, FloatField()))


class IndicatorDataAggregations(AggregationView):
    """
    Returns aggregations based on the item grouped by, and the selected aggregation.

    ## Group by options

    API request has to include `group_by` parameter.
    
    This parameter controls result aggregations and
    can be one or more (comma separated values) of:
    
    - `indicator_category`
    - `indicator`
    - `date_value`
    - `country`
    - `country__region`
    - `country__name`
    - `country__region__name`
    - `unit_of_measure`

    ## Aggregation options

    API request has to include `aggregations` parameter.
    
    This parameter controls result aggregations and
    can be one or more (comma separated values) of:


    - `count`
    - `count_distinct`
    - `measure_value`
    - `mean_value`
    - `max_value`
    - `min_value`

    ## Request parameters

    All filters available on the Activity List, can be used on aggregations.

    """

    queryset = IndicatorDatapoint.objects.all()

    filter_backends = (SearchFilter, DjangoFilterBackend,)
    filter_class = IndicatorDataFilter
    
    fields = (
        'id',
        'file',
        'date_format',
        'indicator',
        'country',
        'date_value',
        'source',
        'measure_value',
        'unit_of_measure',
    )

    allowed_aggregations = (
        Aggregation(
            query_param='count',
            field='count',
            annotate=Count('id'),
        ),
        Aggregation(
            query_param='count_distinct',
            field='count',
            annotate=Count('id', distinct=True),
        ),
        Aggregation(
            query_param='measure_value',
            field='total_measure',
            annotate=annotate_measure,
        ),
        Aggregation(
              query_param='mean_value',
            field='total_measure',
            annotate=mean_measure,
        ),
        Aggregation(
            query_param='max_value',
            field='total_measure',
            annotate=max_measure,
        ),
        Aggregation(
            query_param='min_value',
            field='total_measure',
            annotate=min_measure,
        ),
    )

    allowed_groupings = (
        GroupBy(
            query_param="indicator",
            fields=("indicator", "file__data_source__name"),
            # renamed_fields=("indicator", "source"),
        ),
        GroupBy(
            query_param="date_value",
            fields="date_value",
        ),
        GroupBy(
            query_param="country",
            fields="country",
        ),
        GroupBy(
            query_param="country__region",
            fields="country__region",
        ),
        GroupBy(
            query_param="country__name",
            fields="country__name",
        ),
        GroupBy(
            query_param="country__region__name",
            fields="country__region__name"
        ),
        GroupBy(
            query_param="unit_of_measure",
            fields="unit_of_measure",
        ),        
    )

    def get_queryset(self):
        #filter according to filter tag
        return check_filters(self)
