from django.db import OperationalError, connections
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(('GET',))
def overview(request, format=None):
    """
    ### ZOOM-CSV-MAPPER Rest API ###

    The REST API provides programmatic access to read (and soon also write) indicator data.
    The REST API responses are available in JSON.

    ## Available endpoints

    * Indicators: [`/api/indicators`](/api/indicators)

    """
    return Response('TODO go to api/')

@api_view(('GET',))
def welcome(request, format=None):
    """
    ## REST API

    The REST API provides programmatic access to read (and soon also write) indicator data.
    The REST API responses are available in JSON.

    ## Available endpoints

    * Indicators: [`/api/indicators`](/api/indicators)

    """
    return Response('''{
        'endpoints': {
            'indicators': reverse(
                'indicators:indicator-list',
                request=request,
                format=format),
            'file': reverse(
                'file:file-source-list',
                request=request,
                format=format),
            'validate': reverse(
                'validate:validate',
                request=request,
                format=format),
            'manual-mapper': reverse(
                'manual-mapper:manual-mapper',
                request=request,
                format=format),
        }
    }''')



@api_view(('GET',))
def health_check(request, format=None):
    """
    Performs an API health check
    """
    okay = True

    conn = connections['default']
    try:
        c = conn.cursor()
    except OperationalError:
        okay = False

    if okay is False:
        return Response(status=500)

    return Response(status=200)
