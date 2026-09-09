"""Report-file fields are usable from the model instance, and wide enough.

Intent: a report column is declared ``report = XLSXField(null=True, blank=True)``
and written from ``calculate()``. Two things a customer reasonably expects of
that column, neither of which held:

1. **The helper is reachable from the value.** ``create_excel_file_from_dfs``
   is written against a *FieldFile* — it ends in ``self.save(name, content,
   save=False)`` — yet it lived only on the field class, so
   ``self.report.create_excel_file_from_dfs(...)`` raised ``AttributeError:
   'FieldFile' object has no attribute 'create_excel_file_from_dfs'`` and only
   the unbound ``XLSXField.create_excel_file_from_dfs(self.report, ...)``
   worked. Both spellings must work, and the unbound one must keep resolving
   to the same code — every Lex app in the field uses it.
2. **The column fits the paths reports generate.** ``XLSXField.max_length =
   300`` was dead: ``FileField.__init__`` setdefaults it to 100 and
   ``Field.__init__`` then shadows the class attribute, so every bare
   ``XLSXField()`` was ``varchar(100)``. Over that length Django's storage
   layer *silently truncates and suffixes* the filename rather than raising —
   a report quietly lands under a name nobody asked for.

Why a regression matters: both failure modes are silent or opaque at the point
of use and only surface in production, inside a Celery worker, as a stack
trace that names no code the customer wrote.

Cluster 13h — scenarios 13.38–13.45. Type: I.
Covers: lex/core/fields/XLSX_field.py, lex/core/fields/PDF_field.py.
Run: python -m lex pytest lex/test_project/tests/exports/test_13h_xlsx_field_binding.py -v
"""

from __future__ import annotations

import pickle
import shutil
import tempfile

import pandas as pd
import pytest
from django.db.models.fields.files import FieldFile
from django.test import SimpleTestCase, override_settings

from lex.core.fields.PDF_field import PDFField
from lex.core.fields.XLSX_field import XLSXField, XLSXFieldFile
from lex.test_project.tests._e2e_test_case import E2ETestCase

from .models import XlsxReportProbe

pytestmark = pytest.mark.exports

# Report writes are a storage side-effect; keep them out of the working tree.
MEDIA_ROOT = tempfile.mkdtemp(prefix="lex-13h-")

# 122 characters — over Django's 100-char FileField default, under 300.
LONG_REPORT_PATH = (
    "Reports/EndBalancePerPostingTypeReport/"
    + "segment_" * 8
    + "20260905_10_00.xlsx"
)


def tearDownModule():
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


def _frame() -> pd.DataFrame:
    """A report-shaped frame: named index + one numeric column."""
    return pd.DataFrame({"amount": [1.0, 2.0]}).set_index(
        pd.Index(["alpha", "beta"], name="investment")
    )


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TestCluster13h_XlsxFieldBinding(E2ETestCase):
    """Cluster 13h: both spellings of the report write, and what the value is."""

    e2e_models = [XlsxReportProbe]

    def test_13_38_bound_helper_writes_the_report_and_the_name_persists(self):
        """
        Scenario 13.38: writing a report through the field value stores both
        the file and the row.
        Given: a model with a bare ``XLSXField`` report column
        When: ``calculate()`` calls ``self.report.create_excel_file_from_dfs(...)``
              and the framework then saves the model, as ``calc_and_save`` does
        Then: the workbook is in storage and the reloaded row carries its name
        """
        probe = XlsxReportProbe.objects.create(name="bound")

        probe.report.create_excel_file_from_dfs(
            path="Reports/bound_20260905_10_00.xlsx",
            data_frames=[_frame()],
            sheet_names=["Investment Inputs"],
            merge_cells=False,
            index=True,
        )
        probe.save()

        reloaded = XlsxReportProbe.objects.get(pk=probe.pk)
        self.assertEqual(
            reloaded.report.name,
            "Reports/bound_20260905_10_00.xlsx",
            "create_excel_file_from_dfs saves with save=False, so the filename "
            "must reach the database via the framework's own model.save() — "
            "otherwise the file exists but the row points at nothing.",
        )
        self.assertTrue(
            reloaded.report.storage.exists(reloaded.report.name),
            f"The workbook must exist in storage at {reloaded.report.name!r}.",
        )
        written = pd.read_excel(
            reloaded.report.path, sheet_name="Investment Inputs", index_col=0
        )
        self.assertEqual(
            list(written.columns), ["amount"],
            "The stored workbook must contain the frame that was handed in, "
            f"got columns {list(written.columns)!r}.",
        )

    def test_13_39_unbound_helper_still_writes_the_same_report(self):
        """
        Scenario 13.39: the historical call form keeps working unchanged.
        Given: the same report column
        When: written the way every existing Lex app writes it —
              ``XLSXField.create_excel_file_from_dfs(self.report, ...)``
        Then: the file lands identically; making the bound form work must not
              cost the unbound one
        """
        probe = XlsxReportProbe.objects.create(name="unbound")

        XLSXField.create_excel_file_from_dfs(
            probe.report,
            path="Reports/unbound_20260905_10_00.xlsx",
            data_frames=[_frame()],
            sheet_names=["Investment Inputs"],
        )
        probe.save()

        reloaded = XlsxReportProbe.objects.get(pk=probe.pk)
        self.assertEqual(
            reloaded.report.name,
            "Reports/unbound_20260905_10_00.xlsx",
            "The unbound form is the established convention across every Lex "
            "app; it must keep resolving to the same implementation.",
        )
        self.assertTrue(
            reloaded.report.storage.exists(reloaded.report.name),
            "The unbound form must write the workbook to storage too.",
        )

    def test_13_40_field_value_is_still_a_fieldfile(self):
        """
        Scenario 13.40: the value keeps its Django identity.
        Given: a model instance with a report column
        When: the attribute is read
        Then: it is a ``FieldFile`` — audit-log payload serialization branches
              on ``isinstance(v, FieldFile)``, so narrowing that type would
              silently drop file fields out of the audit trail
        """
        probe = XlsxReportProbe(name="identity")

        value = probe.report

        self.assertIsInstance(
            value, FieldFile,
            "Report values must remain FieldFile instances — the audit-logging "
            "serializer dispatches on that type.",
        )
        self.assertIsInstance(
            value, XLSXFieldFile,
            "…and specifically the XLSX subclass, which is what carries the "
            "report helpers.",
        )
        self.assertTrue(
            getattr(type(value).create_excel_file_from_dfs, "alters_data", False),
            "The helper writes to storage, so it must carry Django's "
            "alters_data marker like FieldFile.save/open/delete do.",
        )

    def test_13_41_helper_survives_the_pickle_round_trip(self):
        """
        Scenario 13.41: the helper is still there after a trip through Celery.
        Given: a saved model instance carrying a report value
        When: pickled and unpickled, as dispatching to a Celery worker does
        Then: the value is still the report-capable class with its name intact
        """
        probe = XlsxReportProbe.objects.create(name="pickled")
        probe.report.name = "Reports/pickled.xlsx"

        revived = pickle.loads(pickle.dumps(probe))

        self.assertIsInstance(
            revived.report, XLSXFieldFile,
            "calc_and_save receives model instances over the broker; if the "
            "class does not survive pickling, the report write fails only in "
            "the worker and never locally.",
        )
        self.assertEqual(
            revived.report.name, "Reports/pickled.xlsx",
            "The file name must survive the round trip unchanged.",
        )
        self.assertTrue(
            callable(revived.report.create_excel_file_from_dfs),
            "The revived value must still expose the report helper.",
        )


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TestCluster13h_LongReportPath(E2ETestCase):
    """Cluster 13h: the column is wide enough for the paths reports build."""

    e2e_models = [XlsxReportProbe]

    def test_13_44_long_report_path_round_trips_untruncated(self):
        """
        Scenario 13.44: a realistic nested report path is stored verbatim.
        Given: a report path of 122 characters — a nested prefix plus a
               timestamped name, the shape reports actually generate
        When: written through the field and reloaded from the database
        Then: the name comes back byte-for-byte; over the column width Django
              silently truncates and suffixes instead of raising, so the file
              would otherwise land under a name the app never chose
        """
        self.assertGreater(
            len(LONG_REPORT_PATH), 100,
            "This scenario is only meaningful if the path exceeds Django's "
            "100-char FileField default.",
        )
        probe = XlsxReportProbe.objects.create(name="long-path")

        probe.report.create_excel_file_from_dfs(
            path=LONG_REPORT_PATH,
            data_frames=[_frame()],
            sheet_names=["Sheet"],
        )
        probe.save()

        reloaded = XlsxReportProbe.objects.get(pk=probe.pk)
        self.assertEqual(
            reloaded.report.name, LONG_REPORT_PATH,
            "The stored name must match the requested path exactly; a "
            "truncated-and-suffixed name means the column is too narrow.",
        )


class TestCluster13h_FileFieldMaxLength(SimpleTestCase):
    """Cluster 13h: the advertised report-column width actually applies."""

    def test_13_42_bare_xlsx_field_defaults_to_the_report_width(self):
        """
        Scenario 13.42: the declared default actually applies.
        Given: ``XLSXField()`` declared with no explicit ``max_length``
        When: the field is constructed
        Then: it is 300 wide, the width the class has always advertised
        """
        field = XLSXField(null=True, blank=True)

        self.assertEqual(
            field.max_length, 300,
            "XLSXField advertises max_length = 300; a bare declaration must "
            f"get it rather than Django's FileField default, got "
            f"{field.max_length}.",
        )

    def test_13_43_explicit_max_length_still_wins(self):
        """
        Scenario 13.43: the default stays a default.
        Given: a report column that asks for a specific width
        When: ``XLSXField(max_length=120)`` is constructed
        Then: the caller's value is kept — apps that sized their columns
              deliberately are not overridden
        """
        field = XLSXField(null=True, blank=True, max_length=120)

        self.assertEqual(
            field.max_length, 120,
            "An explicit max_length must beat the class default, got "
            f"{field.max_length}.",
        )

    def test_13_45_bare_pdf_field_defaults_to_the_report_width(self):
        """
        Scenario 13.45: the sibling report field behaves the same.
        Given: ``PDFField()`` declared with no explicit ``max_length``
        When: the field is constructed
        Then: it is 300 wide — PDF reports build the same nested paths, and
              carrying the same advertised-but-dead default would leave the
              identical trap
        """
        field = PDFField(null=True, blank=True)

        self.assertEqual(
            field.max_length, 300,
            "PDFField advertises max_length = 300 for the same reason "
            f"XLSXField does, got {field.max_length}.",
        )
