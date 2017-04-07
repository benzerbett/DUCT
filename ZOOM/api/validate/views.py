from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.conf import settings
from indicator.models import IndicatorDatapoint
from lib.converters import convert_spreadsheet
from lib.tools import check_column_data, identify_col_dtype, get_line_index
from geodata.importer.country import CountryImport
from geodata.models import get_dictionaries
from django.contrib.staticfiles.templatetags.staticfiles import static
from validate.models import File
import json
import os
import pickle
import uuid
import numpy as np
import pandas as pd
from django.core import serializers


@api_view(['GET', 'POST'])
def validate(request):
    if request.method == 'POST':
        file_id = request.data['file_id']
        print("Here")
    else:
        return Response("No file selected");
    newdoc = ['Item']#tmp 
    validate_form = True
    count = 0
    overall_count = 0
    
    missing_mapping = [] #change name -> doesn't make sense 
    remaining_mapping = []#also doesn't make sense any more
    missing_datatypes = []
    found_mapping = []
    mapping = [] # what does this mean????
    validation_results = []
    dtypes_list = []
    error_lines = []

    dtypes_dict = {}
    headings_template = {}
    headings_file = {}

    count = 0
    newdoc[0] = str(File.objects.get(id=file_id).file)
    #loop here for multiple files
    df_file = pd.read_csv(newdoc[0])#.get_file_path())
    file_heading_list = df_file.columns
    #sample_amount = len(df_file[file_heading_list[0]]) # might be too big, might take too long
    template_heading_list = []
    
    #Get datapoint headings
    for field in IndicatorDatapoint._meta.fields:
        template_heading_list.append(field.name)#.get_attname_column())
    
    template_heading_list = template_heading_list[4:len(template_heading_list)]#skip first four headings as irrelevant to user input
    template_heading_list.append("unit_measure") #needed? 
    
    #count = 0# not sure if this is still needed, might need for matches
    dicts, _ = get_dictionaries()#get dicts for country
    #c = _
    #g = dicts
    for heading in file_heading_list:
        headings_file[heading] = count
        prob_list, error_count = identify_col_dtype(df_file[heading], heading, dicts)
        dtypes_dict[heading] = prob_list 
        
        error_lines.append(error_count)
        validation_results.append(df_file[heading].isnull().sum())
        dtypes_list.append(prob_list) 
        #count += 1

    count = 0 #count matching
    overall_count = len(template_heading_list)

    for key in template_heading_list:
      remaining_mapping.append(key)
    
    files = []
    files_id = []
    files.append(newdoc[0])#.get_file_path())   
    zip_list = zip(file_heading_list, dtypes_list, validation_results)#zip(found_mapping, mapping, data_types, validation_on_types)
    missing_mapping = list(headings_file.keys())
    
    #check this, see if these are relevant 
    #request.session['missing_dtypes_list'] = error_lines #change name # error per column, error[0][0] => 1st column 1st line
    #request.session['found_mapping'] = []#file_heading_list#zip_list
    #request.session['missing_list'] = missing_mapping#change name -> silly
    #request.session['files'] = files
    path = os.path.join(os.path.dirname(settings.BASE_DIR), 'ZOOM/media/tmpfiles')#static('tmpfiles')
    dict_name = path +  "/" + str(uuid.uuid4()) + ".txt"
    with open(dict_name, 'w') as f:
        pickle.dump(dtypes_dict, f)  
    #request.session['dtypes'] = dict_name
    #request.session['template_file'] = template_file
    #request.session['remaining_headings'] = remaining_mapping
    
    context = {'validate': validate_form, 'mapped' : count, "no_mapped" : overall_count - count, "found_list": zip_list, "missing_list" : remaining_mapping, "files" : files[0], "dtypes_loc" : dict_name}#reorganise messy
    #context = {'message':'heya'}

    print(context);
    

    #output need to pass allignments of mapped headings
    return Response(context)

    @api_view(['GET', 'POST'])
    def error_correction(request):
        context = {"Error": "To do"}
        return Response(context)        

    """class Validation(APIView):
    """
    #List all snippets, or create a new snippet.
    """
    def get(self, request, format=None):
        #fill in for returning list if files
        return Response({'Validation': 'List here how to use it?'}, status=200)
        #return Response(json.dumps(workspace))

    #post functions for file
    def post(self, request, format=None):
        if 'validate' in request.data:
            #check if file exists, it it doesn't continue
            file_id = request.data['file_id']
            #context = self.validate(file_id, request)
        result = 1
        print("Yup");
        return Response({"message": "Got some data!", "data": request.data})
        return context #Response({"success": True})
        return Response({'result': data })

    @api_view()
    def validate(self, file_id, request):
        newdoc = ['Item']
        validate_form = True
        count = 0
        overall_count = 0
        
        missing_mapping = [] #change name -> doesn't make sense 
        remaining_mapping = []#also doesn't make sense any more
        missing_datatypes = []
        found_mapping = []
        mapping = [] # what does this mean????
        validation_results = []
        dtypes_list = []
        error_lines = []

        dtypes_dict = {}
        headings_template = {}
        headings_file = {}

        count = 0
        newdoc[0] = str(File.objects.get(id=file_id).file)
        #loop here for multiple files
        df_file = pd.read_csv(newdoc[0])#.get_file_path())
        file_heading_list = df_file.columns
        #sample_amount = len(df_file[file_heading_list[0]]) # might be too big, might take too long
        template_heading_list = []
        
        #Get datapoint headings
        for field in IndicatorDatapoint._meta.fields:
            template_heading_list.append(field.name)#.get_attname_column())
        
        template_heading_list = template_heading_list[4:len(template_heading_list)]#skip first four headings as irrelevant to user input
        template_heading_list.append("unit_measure") #needed? 
        
        #count = 0# not sure if this is still needed, might need for matches
        dicts, _ = get_dictionaries()#get dicts for country
        #c = _
        #g = dicts
        for heading in file_heading_list:
            headings_file[heading] = count
            prob_list, error_count = identify_col_dtype(df_file[heading], heading, dicts)
            dtypes_dict[heading] = prob_list 
            
            error_lines.append(error_count)
            validation_results.append(df_file[heading].isnull().sum())
            dtypes_list.append(prob_list) 
            #count += 1

        count = 0 #count matching
        overall_count = len(template_heading_list)

        for key in template_heading_list:
          remaining_mapping.append(key)
        
        files = []
        files_id = []
        files.append(newdoc[0])#.get_file_path())   
        zip_list = zip(file_heading_list, dtypes_list, validation_results)#zip(found_mapping, mapping, data_types, validation_on_types)
        missing_mapping = list(headings_file.keys())
        
        #check this, see if these are relevant 
        #request.session['missing_dtypes_list'] = error_lines #change name # error per column, error[0][0] => 1st column 1st line
        #request.session['found_mapping'] = []#file_heading_list#zip_list
        #request.session['missing_list'] = missing_mapping#change name -> silly
        #request.session['files'] = files
        path = os.path.join(os.path.dirname(settings.BASE_DIR), 'ZOOM/media/tmpfiles')#static('tmpfiles')
        dict_name = path +  "/" + str(uuid.uuid4()) + ".txt"
        with open(dict_name, 'w') as f:
            pickle.dump(dtypes_dict, f)  
        #request.session['dtypes'] = dict_name
        #request.session['template_file'] = template_file
        #request.session['remaining_headings'] = remaining_mapping
        
        #context = {'validate': validate_form, 'mapped' : count, "no_mapped" : overall_count - count, "found_list": zip_list, "missing_list" : remaining_mapping, "files" : files[0], "dtypes_loc" : dict_name}#reorganise messy
        context = {'message':'heya'}
        #output need to pass allignments of mapped headings
        return Response({"message": "Got some data!", "data": request.data})
        #return context
        #return render(request, 'validate/input_report.html', context)"""