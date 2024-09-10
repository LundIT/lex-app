# from datetime import datetime
#
# import asyncio
# import os
# import traceback
# from glob import glob
#
# from pathlib import Path
#
# from lex.lex_app.lex_models.Created_by_model import CreatedByMixin
# from lex.lex_app.lex_models.Process import Process
# from lex.lex_app.rest_api.signals import custom_post_save
# from lex.lex_app.rest_api.views.model_entries import One
# from django.db.models import Model, AutoField, TextField, FloatField, DateTimeField, ForeignKey, CASCADE, FileField, \
#     IntegerField, BooleanField
#
# from lex.lex_app.rest_api.fields.HTML_field import HTMLField
# from lex.lex_app.rest_api.fields.PDF_field import PDFField
# from lex.lex_app.rest_api.fields.XLSX_field import XLSXField
# from lex.lex_app.rest_api.fields.Bokeh_field import BokehField
#
# from lex_app import settings
# from lex.lex_app.lex_models.calculated_model import CalculatedModelMixin
# from lex.lex_app.lex_models.html_report import HTMLReport
import os

# from lex.lex_app.lex_models.upload_model import UploadModelMixin, ConditionalUpdateMixin
# from django.db.models import Model
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
#
# from lex_app.ProcessAdminSettings import processAdminSite, adminSite
# from asgiref.sync import sync_to_async
# import nest_asyncio
#
# print("Importing sys")
# import sys
#
# model_structure = {}
# model_styling = {}
# global_filter_structure = {}
#
#
# def insert_model_to_structure(current_model_struct, path, name):
#     path_split = path.split('.')
#     for p in path_split:
#         if p not in current_model_struct:
#             current_model_struct[p] = {}
#         current_model_struct = current_model_struct[p]
#
#     current_model_struct[name] = None
#
#
# def shorten_model_structure(current_model_struct):
#     """
#     removes all common directories at the beginning as long as they do not contain single models
#     :param current_model_struct:
#     :return:
#     """
#
#     def get_first_dict_value(my_dict):
#         return next(iter(my_dict.values())) if len(my_dict.keys()) > 0 else None
#
#     def dict_is_leaf(my_dict):
#         return get_first_dict_value(my_dict) is None
#
#     while len(current_model_struct.keys()) == 1 and not dict_is_leaf(get_first_dict_value(current_model_struct)):
#         current_model_struct = next(iter(current_model_struct.values()))
#     return current_model_struct
#
#
# def is_special_file(file):
#     return (file.stem.endswith("_test") or
#             file.parents[0].name == "migrations" or
#             file.stem.endswith("create_db") or
#             file.stem.endswith("Log") or
#             file.stem.endswith("Streamlit") or
#             file.stem.endswith("CalculationIDs"))
#
#
# def is_included_in_model_structure(file):
#     return not file.stem.endswith("model_structure") and not file.stem.endswith(
#         "authentication_settings") and not is_special_file(file)
#
# # class User(AbstractUser):
# #    identifier = models.CharField(max_length=200, unique=True)
#
#
# # Find all files in submodels and import them via exec
# # Find the app name as the nameof the directory this file is in
#
# # importing those tables for all projects
# from django.contrib.auth.models import User, Group, Permission
# from django.contrib.contenttypes.models import ContentType
#
# processAdminSite.register([User, Group, Permission, ContentType])
#
# app_name = Path(__file__).resolve().parent.parts[-1]
#
# # Find all files in submodels
# base_path = Path(os.getenv("PROJECT_ROOT")).resolve()
# # List all .py files, excluding those in 'venv' directory and starting with '_'
# files = [f for f in base_path.glob("./**/[!_]*.py") if 'venv' not in f.parts and '.venv' not in f.parts and 'build' not in f.parts]
# from lex.lex_app.logging.UserChangeLog import UserChangeLog
# from lex.lex_app.logging.CalculationLog import CalculationLog
# from lex.lex_app.logging.CalculationIDs import CalculationIDs
# from lex.lex_app.logging.Log import Log
# from lex.lex_app.logging.Streamlit import Streamlit
#
# # migrations need to lie on the top level of the repository. Therefore, the
# repo_name = settings.repo_name
# settings.MIGRATION_MODULES[repo_name] = f'{repo_name}.migrations'
#
# processAdminSite.register([UserChangeLog, CalculationIDs, CalculationLog, Streamlit, Log])
# adminSite.register([UserChangeLog, CalculationIDs, CalculationLog, Log])
# processAdminSite.registerHTMLReport("streamlit", Streamlit)
#
# model_structure_defined = False
# auth_settings = None
# widget_structure = []
# i = 0
# while i < len(files):
#     file = files[i]
#     i += 1
#     name = file.stem
#     subfolders = '.'.join(file.parts[file.parts.index(repo_name) + 1 :-1])
#     if not is_special_file(file):
#         try:
#             # TODO ensure that no wrong things can be imported here. #Security Issue
#
#             if name.endswith('model_structure'):
#                 exec(f"import {subfolders}.{name} as {name}")
#                 imported_file = eval(name)
#                 if (hasattr(imported_file, "get_model_structure")):
#                     model_structure = imported_file.get_model_structure()
#                     model_structure_defined = True
#                 if (hasattr(imported_file, "get_widget_structure")):
#                     widget_structure = imported_file.get_widget_structure()
#                 if (hasattr(imported_file, "get_model_styling")):
#                     model_styling = imported_file.get_model_styling()
#                 if (hasattr(imported_file, "get_global_filter_structure")):
#                     global_filter_structure = imported_file.get_global_filter_structure()
#
#             else:
#                 exec(f"from {subfolders}.{name} import {name}")
#                 imported_class = eval(name)
#                 if issubclass(imported_class, HTMLReport):
#                     processAdminSite.registerHTMLReport(name.lower(), imported_class)
#                     processAdminSite.register([imported_class])
#
#                 elif issubclass(imported_class, Process):
#                     processAdminSite.registerProcess(name.lower(), imported_class)
#                     processAdminSite.register([imported_class])
#
#                 elif not issubclass(imported_class, type) and imported_class._meta.abstract is not True:
#                     processAdminSite.register([imported_class])
#                     adminSite.register([imported_class])
#
#                     # Below part should be updated with the new use case dpag pip
#
#                     if issubclass(imported_class, ConditionalUpdateMixin):
#
#                         if os.getenv("CALLED_FROM_START_COMMAND"):
#                             @sync_to_async
#                             def reset_instances_with_aborted_calculations():
#                                 if not os.getenv("CELERY_ACTIVE"):
#                                     aborted_calc_instances = imported_class.objects.filter(calculate=True)
#                                     aborted_calc_instances.update(calculate=False)
#
#                             nest_asyncio.apply()
#                             loop = asyncio.get_event_loop()
#                             loop.run_until_complete(reset_instances_with_aborted_calculations())
#                     #
#                     # if not model_structure_defined:
#                     #    insert_model_to_structure(model_structure, subfolders, imported_class._meta.model_name)
#
#         except NameError as e:
#             # If the current file can't be imported, put it in the end of the line hoping that we will clear the dependecies later
#             if not i >= len(files) - 1:
#                 files.append(file)
#             else:
#                 traceback.print_exc()
#         except AttributeError:
#             # If the current file can't be imported, put it in the end of the line hoping that we will clear the dependecies later
#             if not i >= len(files) - 1:
#                 files.append(file)
#             else:
#                 traceback.print_exc()
#
# try:
#     mod_files = list(Path.cwd().glob("**/_authentication_settings.py"))
#     if len(mod_files) == 1:
#         mod_file = mod_files[0]
#         name = mod_file.stem
#         subfolders = '.'.join(mod_file.parts[mod_file.parts.index(repo_name) + 1: -1])
#         exec(f"from {name} import create_groups")
#         imported_function = eval("create_groups")
#         imported_function()
# except Exception:
#     pass
#
# auth_files = list(Path.cwd().glob("**/_authentication_settings.py"))
# if len(auth_files) > 0:
#     auth_file = auth_files[0]
#     name = auth_file.stem
#     subfolders = '.'.join(auth_file.parts[auth_file.parts.index(repo_name) + 1: -1])
#     exec(f"import {subfolders}.{name} as {name}")
#     auth_settings = eval(name)
#
# if not model_structure_defined:
#     sorted_files = sorted(files)
#     for file in sorted_files:
#         name = file.stem
#         subfolders = '.'.join(file.parts[file.parts.index(repo_name) + 1: -1])
#         if is_included_in_model_structure(file):
#             imported_class = eval(name)
#             if issubclass(imported_class, HTMLReport):
#                 insert_model_to_structure(model_structure, subfolders, name.lower())
#             elif issubclass(imported_class, Process):
#                 insert_model_to_structure(model_structure, subfolders, name.lower())
#             elif not issubclass(imported_class, type) and imported_class._meta.abstract is not True:
#                 insert_model_to_structure(model_structure, subfolders, imported_class._meta.model_name)
#
# model_structure = shorten_model_structure(model_structure)
# model_structure['Z_Reports'] = {'userchangelog': None, 'calculationlog': None, 'log': None}
# if os.getenv("IS_STREAMLIT_ENABLED") == "true":
#     model_structure['Streamlit'] = {'streamlit': None}
#
#
# processAdminSite.register_model_structure(model_structure)
# processAdminSite.register_model_styling(model_styling)
# processAdminSite.register_global_filter_structure(global_filter_structure)
#
# print(f"checking for runserver, {sys.argv}")
# if sys.argv[1:2] == ["runserver"]:
#     # Something specific to running "test"
#     print("In runserver conditional")
#     try:
#         from rest_framework_api_key.models import APIKey
#
#         print("Checking for number of API-keys")
#         if APIKey.objects.count() == 0:
#             print("Creating API-key")
#             api_key, key = APIKey.objects.create_key(name='APIKey')
#             print("API_KEY:", key)
#         else:
#             print("API_KEY already exists")
#     except Exception as e:
#         print(traceback.print_exc())
#
# TODO: Move it Somewhere and delete this file
# @receiver(post_save)
# def update_handler(sender, **kwargs):
#     if issubclass(sender, UploadModelMixin):
#         update_method = kwargs["instance"].update
#         if (hasattr(update_method, 'delay') and
#                 os.getenv("DEPLOYMENT_ENVIRONMENT") and
#                 os.getenv("ARCHITECTURE") == "MQ/Worker"):
#             # @custom_shared_task decorator is used
#             update_method.delay(kwargs["instance"])
#         else:
#             # @custom_shared_task decorator is not used
#             sender.update(kwargs["instance"])
#
# # @receiver(post_delete)
# # def delete_file(sender, instance, **kwargs):
# #     """
# #     Whenever a model instance is deleted, check if it has 'file' attribute and if so,
# #     deletes the file too.
# #     """
# #     if os.getenv("STORAGE_TYPE") and os.getenv("STORAGE_TYPE") != "LEGACY":
# #         for f in instance._meta.get_fields():
# #             if isinstance(f, FileField):  # Check if the field is FileField
# #                 file_field = instance._meta.get_field(f.name)
# #                 field_value = file_field.value_from_object(instance)
# #                 if field_value and hasattr(field_value, 'name'):
# #                     file_field.storage.delete(field_value.name)
# #
# # @receiver(pre_save)
# # def delete_old_file_on_change(sender, instance, **kwargs):
# #     if os.getenv("STORAGE_TYPE") and os.getenv("STORAGE_TYPE") != "LEGACY":
# #         if not issubclass(sender, Model):
# #             return
# #
# #         try:
# #             # getting the instance from the database, if exists.
# #             # if the instance is not in the database yet, we skip the function.
# #             obj = sender.objects.get(pk=instance.pk)
# #         except sender.DoesNotExist:
# #             return
# #
# #         for field in sender._meta.get_fields():
# #             if not isinstance(field, FileField):  # Check if the field is FileField
# #                 continue
# #
# #             try:
# #                 instance_file = getattr(instance, field.name)
# #                 obj_file = getattr(obj, field.name)
# #
# #                 if instance_file != obj_file and obj_file.name:
# #                     obj_file.storage.delete(obj_file.name)
# #             except (AttributeError, ValueError):
# #                 continue
#
#
