import datetime
import io
import os
from functools import wraps

import pandas as pd
from celery import current_task
from django.core.files import File
from django.core.files.storage import default_storage
from django.db import models

from lex.lex_app.lex_models.ModificationRestrictedModelExample import AdminReportsModificationRestriction
from lex.lex_app.lex_models.calculated_model import CalculatedModelMixin
from lex.lex_app.logging.CalculationIDs import CalculationIDs
from lex.lex_app.logging.CalculationLog import CalculationLog
from lex.lex_app.rest_api.context import context_id
from lex.lex_app.rest_api.fields.XLSX_field import XLSXField
from lex.lex_app.rest_api.helpers import convert_dfs_in_excel


class Log(CalculatedModelMixin, models.Model):
    """
    A Django model for logging calculation processes and their results.

    Attributes
    ----------
    modification_restriction : AdminReportsModificationRestriction
        Restriction for modifying the log.
    id : AutoField
        Primary key for the log entry.
    group : TextField
        Group identifier for the log entry.
    logfile : XLSXField
        Path to the logfile.
    input_validation : XLSXField
        Path to the input validation file.
    t0 : datetime
        Timestamp of log creation.
    defining_fields : list
        Fields that define the log entry.
    filter : list
        Filter criteria for the log entry.

    Methods
    -------
    log(function)
        Decorator to automatically trigger the creation of a log entry.
    get_selected_key_list(key: str) -> list
        Get a list of selected keys based on the provided key.
    get_calculation_id(calculation_model)
        Get the calculation ID for the given calculation model.
    calculate(*args)
        Perform the calculation and log the results.
    preprocess_log_df(logs, message_df, traces)
        Preprocess the log DataFrame.
    preprocess_input_val_df(df)
        Preprocess the input validation DataFrame.
    update_dfs_for_excel(new_dict, path)
        Update DataFrames for Excel export.
    set_levels(logs, trace_len, n_row)
        Set the levels for the log entries.
    set_delta(logs, trace_len)
        Calculate the time difference between start and finish log entries.
    time_tracking(logs, level)
        Track the time spent on each log entry.
    delete_old_entries()
        Delete old log entries.
    """
    modification_restriction = AdminReportsModificationRestriction()
    id = models.AutoField(primary_key=True)
    group = models.TextField(null=True)
    logfile = XLSXField(default='', max_length=300)
    input_validation = XLSXField(default='', max_length=300)

    t0 = datetime.datetime.now()

    defining_fields = ['group']

    filter = []

    class Meta:
        app_label = 'lex_app'

    @staticmethod
    def log(function):
        """
        Decorator to automatically trigger the creation of a log entry.

        Parameters
        ----------
        function : callable
            The function to be wrapped by the log decorator.

        Returns
        -------
        callable
            The wrapped function.
        """
        # This function automatically triggers the creation of Log if set as a wrapper for the respective function it should be used in
        # The class in which it should be used needs to have a function
        # get_log_filter(self):
        #    return self.__str__()
        @wraps(function)
        def wrap(*args, **kwargs):
            self = args[0]
            if hasattr(self, 'get_log_filter'):
                if (hasattr(function, 'delay') and
                    os.getenv("DEPLOYMENT_ENVIRONMENT")
                        and os.getenv("ARCHITECTURE") == "MQ/Worker"):
                    obj = CalculationIDs.objects.filter(context_id=context_id.get()['context_id']).first()
                    calculation_id = getattr(obj, "calculation_id", "test_id")
                    return_value = function.apply_async(args=args, kwargs=kwargs,
                                                        task_id=str(calculation_id))
                    self.celery_result = return_value
                else:
                    log_filter = self.get_log_filter()
                    return_value = function(*args, **kwargs)
                    Log.create(filter=[log_filter[0]], group=[log_filter[1]], *args)

                return return_value
            else:
                return None

        return wrap

    def get_selected_key_list(self, key: str) -> list:
        """
        Get a list of selected keys based on the provided key.

        Parameters
        ----------
        key : str
            The key to get the selected list for.

        Returns
        -------
        list
            The list of selected keys.
        """
        if key == 'group':
            return [self.group]

    @classmethod
    def get_calculation_id(self, calculation_model):
        """
        Get the calculation ID for the given calculation model.

        Parameters
        ----------
        calculation_model : Model
            The calculation model to get the ID for.

        Returns
        -------
        str
            The calculation ID.
        """
        return f"{str(calculation_model._meta.model_name)}-{str(calculation_model.id)}" if calculation_model is not None else "test_id"

    def calculate(self, *args):
        """
        Perform the calculation and log the results.

        Parameters
        ----------
        *args : tuple
            Arguments for the calculation.
        """
        dfs = []
        ts_dfs = []
        val_dfs = []
        sheet_names = []
        ts_sheet_names = []
        val_sheet_names = []
        df_dict_new = {}
        ts_dict_new = {}
        val_df_dict_new = {}
        path = "calculation_logs_download/full_logs/" + f"""CalculationLogs_{self.group}.xlsx"""
        path_ts = "calculation_logs_download/time_sheets/" + f"""TimeSheet_{self.group}.xlsx"""
        path_iv = "calculation_logs_download/input_validation/" + f"""InputValidation_{self.group}.xlsx"""
        self.filter = args[0].get_log_filter()[0]
        for element in self.filter:
            if current_task and os.getenv("CELERY_ACTIVE"):
                calculation_id = str(current_task.request.id)
            else:
                obj = CalculationIDs.objects.filter(
                    calculation_record=f"{args[0]._meta.model_name}_{args[0].pk}").first()
                calculation_id = getattr(obj, "calculation_id", "test_id")
            logs = pd.DataFrame.from_records(CalculationLog.objects.filter(calculationId=calculation_id, method__contains=element).values().order_by('timestamp'))

            if len(logs) > 0 and 'create' not in calculation_id:

                # These lines split the message up in severity and content, refer to CalculationLog.py for deeper explanations
                new = logs['message'].str.split(": ", expand=True)
                # We catch incomplete statements with this. But in the future, the correct use of all CalculationLog.create statement makes this superfluous
                if new.shape[1] == 1:
                    message_df = pd.DataFrame({'Severity': 'Success', 'Content': new[0]})
                else:
                    message_df = pd.DataFrame({'Severity': new[0], 'Content': new[1]})

                # This line splits up the method in the different levels, i.e. classes from which the create-statement is called
                traces = logs['method'].str.replace("'", "").str.replace("\[", "").str.replace("\]", "").str[:-1].str[1:].str.split("\), \(", expand=True)
                num_columns = traces.shape[1]
                new_columns = ['level_' + str(i) for i in range(num_columns)]
                traces.columns = new_columns
                # Gets the number of levels
                trace_len = traces.shape[1] - 1
                # Creates the logs DataFrame
                logs = self.preprocess_log_df(logs, message_df, traces)
                # Gets the number of rows in the logs DF
                n_row = logs.shape[1]
                # Sets the level for each entry in the DF; Level is level from the class in which the Log is created, starting with this class at 0 and increasing with each
                # class that is called by 1
                self.set_levels(logs, trace_len, n_row)
                # This is a function for time-tracking
                self.set_delta(logs, trace_len)
                # Drop more unneeded columns
                logs.drop(columns=['calculationId', 'is_notification'], inplace=True)

                # This is a report containing all entries in the logs DF
                dfs.append(logs)
                sheet_names.append(element.split(' | ')[0])
                # Create a dict with all dfs and their sheet names
                df_dict_new[element.split(' | ')[0]] = logs

                # This is a report containing only the time tracking part
                ts = logs.loc[(logs['Severity'] == 'Start') | (logs['Severity'] == 'Finish')]
                if not ts.empty:
                    # Reset the index
                    ts.reset_index(drop=True, inplace=True)
                    ts_dfs.append(ts)
                    ts_sheet_names.append(element.split(' | ')[0])
                    ts_dict_new[element.split(' | ')[0]] = ts

                # This is a report with only the Input validation logs in it
                input_validation = logs.loc[(logs['message_type'] == 'Input Validation')]
                if not input_validation.empty:
                    input_validation = self.preprocess_input_val_df(input_validation)
                    val_dfs.append(input_validation)
                    val_sheet_names.append(element.split(' | ')[0])
                    val_df_dict_new[element.split(' | ')[0]] = input_validation

        if default_storage.exists(path):
            [dfs, sheet_names] = self.update_dfs_for_excel(df_dict_new, path)

        XLSXField.create_excel_file_from_dfs(self.logfile, path, dfs, sheet_names)

        if default_storage.exists(path_ts):
            [ts_dfs, ts_sheet_names] = self.update_dfs_for_excel(ts_dict_new, path_ts)

        if not default_storage.exists("calculation_logs_download/time_sheets/"):
            default_storage.save("calculation_logs_download/time_sheets/" + 'dummy.txt',
                                 content=File(io.BytesIO(), name='dummy.txt'))
            default_storage.delete("calculation_logs_download/time_sheets/" + 'dummy.txt')

        convert_dfs_in_excel(path_ts, ts_dfs, ts_sheet_names)

        if default_storage.exists(path_iv):
            [val_dfs, val_sheet_names] = self.update_dfs_for_excel(val_df_dict_new, path_iv)

        XLSXField.create_excel_file_from_dfs(self.input_validation, path_iv, val_dfs, val_sheet_names)

    @staticmethod
    def preprocess_log_df(logs, message_df, traces):
        """
        Preprocess the log DataFrame.

        Parameters
        ----------
        logs : DataFrame
            The log DataFrame.
        message_df : DataFrame
            The message DataFrame.
        traces : DataFrame
            The traces DataFrame.

        Returns
        -------
        DataFrame
            The preprocessed log DataFrame.
        """
        # Concatenate the logs with the message_df
        logs = pd.concat([logs, message_df], axis=1)
        # Create new column for the level and set it to -1
        logs['Level'] = -1
        # Create new column for the time spent and set it to 0
        logs['Time spent [s]'] = 0
        # Concatenate the logs with the traces
        logs = pd.concat([logs, traces], axis=1)
        # Drop unneeded columns
        logs.drop(columns=['id', 'method', 'message'], inplace=True)
        return logs

    @staticmethod
    def preprocess_input_val_df(df):
        """
        Preprocess the input validation DataFrame.

        Parameters
        ----------
        df : DataFrame
            The input validation DataFrame.

        Returns
        -------
        DataFrame
            The preprocessed input validation DataFrame.
        """
        # Reset the index
        df.reset_index(drop=True, inplace=True)
        # Drop unneeded columns
        df.drop(columns=['timestamp', 'Level', 'Time spent [s]'], inplace=True)
        # Drop all columns that start with level
        level_columns = list(df.filter(regex=r'^level'))
        df.drop(columns=level_columns, inplace=True)
        return df

    @staticmethod
    def update_dfs_for_excel(new_dict, path):
        """
        Update DataFrames for Excel export.

        Parameters
        ----------
        new_dict : dict
            Dictionary of new DataFrames.
        path : str
            Path to the existing Excel file.

        Returns
        -------
        list
            Updated DataFrames and sheet names.
        """
        # Read the existing file and save each sheet as a df to a dict, with the sheet name as keyü
        with default_storage.open(path, 'rb') as file:
            dict_old = pd.read_excel(file, sheet_name=None)
        # If there's a column called Unnamed: 0, drop it
        for key in dict_old.keys():
            if 'Unnamed: 0' in dict_old[key].columns:
                dict_old[key].drop(columns=['Unnamed: 0'], inplace=True)
        # Update the dict with the new dfs
        dict_old.update(new_dict)
        # Save all dfs to a list and save the keys as a list called sheet_names
        dfs = list(dict_old.values())
        sheet_names = list(dict_old.keys())
        # Delete the old file
        default_storage.delete(path)
        # Return the updated dfs and sheet_names
        return [dfs, sheet_names]

    def set_levels(self, logs, trace_len, n_row):
        """
        Set the levels for the log entries.

        Parameters
        ----------
        logs : DataFrame
            The log DataFrame.
        trace_len : int
            The length of the trace.
        n_row : int
            The number of rows in the log DataFrame.
        """
        for index, row in logs.iterrows():
            level = trace_len
            for i in range(n_row, 7, -1):
                if logs.iloc[index, i - 1] is None:
                    level -= 1
                else:
                    logs['Level'][index] = level

    def set_delta(self, logs, trace_len):
        """
        Calculate the time difference between start and finish log entries.

        Parameters
        ----------
        logs : DataFrame
            The log DataFrame.
        trace_len : int
            The length of the trace.
        """
        # If we use the severities START and FINISH from Calculation Log, we can track the time needed to perform a calculation, creation or upload
        # The following method calculates the time difference between the start and responding finish statements
        if trace_len > 0:
            # We use trace_len + 1 to get the last level as well, since range does not include the stop value
            for level in range(0, trace_len + 1):
                assert f"Same number of starts and finishes"
                self.time_tracking(logs, level)
        else:
            level = 0
            self.time_tracking(logs, level)

    def time_tracking(self, logs, level):
        """
        Track the time spent on each log entry.

        Parameters
        ----------
        logs : DataFrame
            The log DataFrame.
        level : int
            The level of the log entry.
        """
        # The time difference is only meaningful if performed on one level, therefore we filter for each level and use those entries only
        same_level_logs = logs[logs['Level'] == level]
        # This is a list containing all indices of the finish entries
        finish_index = list((same_level_logs[same_level_logs['Severity'] == "Finish"]).index)
        # This is a list containing all indices of the start entries
        start_index = list((same_level_logs[same_level_logs['Severity'] == "Start"]).index)
        # They have to be equal in length, if not there would be either a start or finish be missing
        assert len(finish_index) == len(start_index), f"Not same length in indices"
        # Auxiliary variable for iterating
        i = 0
        while i < len(start_index):
            # We use the last start index
            s_i = start_index[-(i + 1)]
            # We now get all entries with the same level, the finish tag and who do not have a time assigned to it
            # This prevents us from matching wrong pairs
            finish_index_without_time = list(logs[(logs['Level'] == level) & (logs['Severity'] == "Finish") & (logs["Time spent [s]"] == 0)].index)
            # We get now the first entry from the above list that has a higher index than the start s_i
            f_i = list(filter(lambda index: index > s_i, finish_index_without_time))[0]
            # We get the difference in timestamps
            dt = logs['timestamp'][f_i] - logs['timestamp'][s_i]
            # And convert it into a nice format
            logs['Time spent [s]'][f_i] = dt.components.minutes * 60 + dt.components.seconds + dt.components.milliseconds / 1000
            # Increase iterator
            i += 1

    @classmethod
    def delete_old_entries(cls):
        """
        Delete old log entries.
        """
        CalculationLog.objects.all().delete()