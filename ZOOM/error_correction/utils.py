import json

import numpy as np

from lib.common import (get_dtype_data, get_file_data,
                        get_geolocation_dictionary, save_validation_data)
from lib.tools import get_prob_list, identify_col_dtype, update_cell_type
from metadata.models import File
from validate.validator import validate

# Updating a cell or file column heading
UPDATE_DICT = {
    'changeHeader': '',
    'header_value': '',
    'header_tobe_changed': '',
    'column': '',
    'line_no': 0,
    'cell_value': '',
}

# For deleting all rows
DELETE_DICT = {
    'row_keys': []
}

# Main dictionary sed for making call
ERROR_CORRECTION_DICT = {
    'file_id': '',
    'start_pos': 0,  # pagination
    'end_pos': 10,
    'type': 'csv',
    'find_value': '',
    'filter_column_heading': '',
    'filter_toggle': False,
    'replace_value': '',
    'replace_pressed': False,
    'error_toggle': False,
    'error_data': {},
    'delete': False,
    'delete_data': DELETE_DICT,
    'update': False,
    'update_data': UPDATE_DICT
}


def error_correction(data, error_toggle, error_rows):
    """Gets data needed for error correction."""

    id = data['file_id']
    start_pos = data['start_pos']  # For pagination
    end_pos = data['end_pos']  # For pagination

    # Future: if type is not csv then error correction being performed on data
    # in data base
    if data['type'] == 'csv':
        df_data = get_file_data(id)
        df_columns = df_data.columns

        if data['filter_toggle']:
            df_data = find_and_replace(df_data, data)
        # if data['error_toggle']:#Filter for errors#
        #    df_data = filter_for_errors(df_data, data)

        output_list = []
        org_data = df_data.copy(deep=True)
        # For displaying line numbers
        org_data['line_no'] = org_data.index.values
        org_data = org_data.reset_index()
        df_data = df_data.reset_index()
        counter = 0
        total_amount = 0
        start = start_pos

        if len(df_data.columns) > 1 and not error_toggle:
            # more columns than just index
            total_amount = len(df_data[df_data.columns[0]])

            for start_pos in range(start, end_pos):
                if start_pos > len(df_data[df_data.columns[0]]) - 1:
                    break

                temp_dict = {'line no.': int(org_data['line_no'][start_pos])}
                for column in df_data.columns:
                    temp_dict[column] = str(df_data[column][start_pos])

                output_list.append(temp_dict)
                counter = counter + 1
        elif len(df_data.columns) > 1 and error_toggle:
            # more columns than just index
            total_amount = len(df_data[df_data.columns[0]])

            for row in error_rows[start_pos:end_pos]:
                if row > len(df_data[df_data.columns[0]]) - 1:
                    break

                temp_dict = {'line no.': int(org_data['line_no'][
                                                 row])}

                for column in df_data.columns:
                    temp_dict[column] = str(df_data[column][row])

                output_list.append(temp_dict)

            if output_list:
                error_messages = data['error_data'][
                                     'error_messages'][start_pos:end_pos]
                data['error_data']['error_messages'] = error_messages
                total_amount = len(error_rows)

        context = {
            'data_table': json.dumps(output_list),
            'total_amount': total_amount,
            'columns': df_columns,
            # added json dumps, front end couldn't read original format
            'error_data': data['error_data']}
    else:
        print('not csv')

    return context


def find_and_replace(df_data, data):
    """Searches for a value and replaces if indicated"""
    id = data['file_id']
    # Heading of column being where find and replace is being carried out
    heading = data['filter_column_heading']
    # Might be better to just find it throughout df_data

    if data['find_value'] == 'nan':
        filter_applied = df_data[heading].isnull()
    else:
        temp = df_data[heading]
        temp = temp.astype('str').str.lower()
        filter_applied = np.array(temp == str(data['find_value']).lower())

    if data['replace_pressed']:
        df_data[heading][filter_applied] = data['replace_value']
        column_values = df_data[heading][filter_applied]

        if len(column_values) > 0:
            error_data, dtypes_dict = get_dtype_data(id)
            dicts = get_geolocation_dictionary()
            temp_prob_list, temp_error_counter = identify_col_dtype(
                column_values, heading, dicts)
            dtypes_dict[heading][filter_applied] = temp_error_counter
            error_data[heading] = get_prob_list(dtypes_dict[heading])
            save_validation_data(error_data, id, dtypes_dict)
            update_data(File.objects.get(id=id).file, df_data)
        df_data = df_data[df_data[heading] == data['replace_value']]
    else:
        df_data = df_data[filter_applied]
    return df_data


def filter_for_errors(df_data, data):
    filter_column = data['error_filter_value']
    error_data, dtypes_dict = get_dtype_data(data['id'])
    errors, line_nos = check_dtypes(
        error_data, dtypes_dict, [filter_column], data['start_pos'],
        data['end_pos'])
    return df_data[line_nos[filter_column]]


# Need to apply optimisation here, put filter here
def check_dtypes(error_data, dtypes_dict,
                 column_headings, start_pos=0, end_pos=0):
    """Check cells against the most popular choice"""
    errors = {}
    line_nos = {}

    # Future: Optimise based on amount needed
    if end_pos == 0:
        end_pos = len(error_data[column_headings[0]])

    for i in column_headings:  # minus one for line no
        if not dtypes_dict[i][0][0] == 'blank':
            filter_applied = (error_data[i] != dtypes_dict[i][0][0])
            # [x for x in error_data[i] if (x != dtypes_dict[i][0][0]
            # and (not dtypes_dict[i][0][0] == 'blank'))]#use map
            indexes = error_data[i][filter_applied]
            errors[i] = indexes
            line_nos[i] = filter_applied
        else:
            errors[i] = []
            line_nos[i] = []
    return errors, line_nos

# should combine with error_correction to optimise?


def get_errors(data):
    """
    Gets data that does not match
    the most probable data type found for each column
    """

    error_messages = []
    id = data['file_id']
    start_pos = data['start_pos']
    end_pos = data['end_pos']
    df_data = get_file_data(id)
    column_headings = df_data.columns
    error_data, dtypes_dict = get_dtype_data(id)
    # TODO: Logic BUGS check everything why using if like below
    # First logic error on then save_validation_data.
    # When used test code will be to if
    # When used GraphQL will be to else
    two_index = False
    try:
        errors, line_nos = check_dtypes(error_data, dtypes_dict,
                                        column_headings)
        selection = np.array(range(0, len(error_data[column_headings[0]])))
    except Exception as e:
        errors, line_nos = check_dtypes(dtypes_dict, error_data,
                                        column_headings)
        selection = np.array(range(0, len(dtypes_dict[column_headings[0]])))
        two_index = False

    amount = end_pos - start_pos
    error_rows = []

    for i in errors:

        if len(errors[i]) > 0:
            counter = 0
            try:
                line_no_selection = selection[line_nos[i]]
                # [start_pos:end_pos]
            except Exception as e:
                line_no_selection = None
                pass

            errors_selection = errors[i]  # [start_pos:end_pos]

            # TODO: related above bug related the below
            for j in errors_selection:  # minus one for line no
                try:
                    dtype = dtypes_dict[i][0][0] if two_index \
                        else dtypes_dict[i][0]

                    row = line_no_selection[counter]
                    if row not in error_rows:
                        error_rows.append(row)

                    message = (
                        'Found a ' +
                        j +
                        ' value instead of the most populous value ' +
                        dtype + '.'
                    )
                    line_no = str(row)
                    error_message_row = dict()
                    error_message_row[''.join([line_no, '|', i])] = (
                        message
                    )
                    error_messages.append(error_message_row)
                    counter += 1
                except Exception as e:
                    pass

    context = {'error_messages': error_messages}
    return context, error_rows


def update(id, data):
    """Updates cell that user edits."""
    df_data = get_file_data(id)
    error_data, dtypes_dict = get_dtype_data(id)

    if not data['changeHeader'] == '':
        count = 2
        tmp = data['header_value']
        while tmp in df_data.columns:
            tmp = data['header_value'] + str(count)
            count += 1
        data['header_value'] = tmp
        df_data = df_data.rename(
            columns={
                data['header_tobe_changed']: data['header_value']})
        dtypes_dict[data['header_value']
                    ] = dtypes_dict[data['header_tobe_changed']]
        dtypes_dict.pop(data['header_tobe_changed'], None)
        error_data[data['header_value']
                   ] = error_data[data['header_tobe_changed']]
        error_data.pop(data['header_tobe_changed'], None)
    else:
        heading = data['column']
        line_no = data['line_no']
        df_data[heading][line_no] = data['cell_value']

        # TODO: Logic BUGS check everything why using if like below
        # First logic error on then save_validation_data.
        # When used test code will be to if
        # When used GraphQL will be to else
        if type(error_data[next(iter(error_data))]) == list:
            prob_list, error_count = update_cell_type(
                df_data[heading][line_no],
                dtypes_dict[heading], line_no, heading
            )
        else:
            prob_list, error_count = update_cell_type(
                df_data[heading][line_no],
                error_data[heading], line_no, heading
            )

        dtypes_dict[heading] = error_count
        error_data[heading] = prob_list

    save_validation_data(error_data, id, dtypes_dict)
    update_data(File.objects.get(id=id).file, df_data)

    return {'success': 1}


def delete_data(id, data):
    """Deletes data based on data"""
    df_data = get_file_data(id)
    row_keys = list(map(int, data['row_keys']))
    df_data = df_data.drop(df_data.index[row_keys])
    df_data = df_data.reset_index(drop=True)
    error_data, dtypes_dict = get_dtype_data(id)
    error_data, dtypes_dict = remove_entries(error_data, dtypes_dict, row_keys)
    save_validation_data(error_data, id, dtypes_dict)
    update_data(File.objects.get(id=id).file, df_data)
    return {'success': 1}


def remove_entries(error_data, dtypes_dict, row_keys):
    """Remove rows from error_data and dtypes_dict"""
    # TODO: really very bad logic
    # How to in old data using the error data to manipulation data
    # for i in error_data:
    #    error_data[i] = \
    #        error_data[i].drop(error_data[i].index[row_keys]).reset_index(
    #            drop=True)
    #    # np.delete(np.array(error_data[i]), row_keys).reset_index()
    #    dtypes_dict[i] = get_prob_list(error_data[i])
    for i in dtypes_dict:
        dtypes_dict[i] = \
            dtypes_dict[i].drop(dtypes_dict[i].index[row_keys]).reset_index(
                drop=True)
        # np.delete(np.array(error_data[i]), row_keys).reset_index()
        dtypes_dict[i] = get_prob_list(dtypes_dict[i])
    return error_data, dtypes_dict


def update_data(file_loc, df_data):
    """Updates data at location file_loc"""
    with open(str(file_loc), 'w') as f:
        df_data.to_csv(f, index=False)
