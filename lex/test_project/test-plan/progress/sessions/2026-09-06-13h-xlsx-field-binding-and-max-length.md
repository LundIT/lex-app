---
date: 2026-09-06
clusters: [13]
tests_added: 8
suite_tally: "13h: 8 pass / 0 fail; exports + serializers + audit_logging + crud_api: 264 pass / 2 xfail / 58 subtests; calculations + api_layer + celery_async: 433 pass / 7 skip / 39 subtests"
---

# Batch 13h — The report column that could not be written to, and was too narrow

Came in from a customer traceback, not from the plan.
[Batch 13g](../../clusters/13-exports/batches.md) fixed the timezone half of
`XLSX_field.py`; this one covers the two things about the same field a customer
hits *before* they get anywhere near a datetime.

## The error named nothing the customer wrote

```
AttributeError: 'FieldFile' object has no attribute 'create_excel_file_from_dfs'
```

raised inside a Celery worker, surfaced through `WaitForTasks` → `result.get()`,
in an app whose own code contains no reference to `FieldFile` at all. That is the
whole problem: `FieldFile` is Django's, and it is what you unavoidably get when
you read a file field off a model instance. The customer had written the obvious
thing — `self.report.create_excel_file_from_dfs(...)` — and there was no way to
tell from the message that the framework wanted
`XLSXField.create_excel_file_from_dfs(self.report, ...)` instead.

Both spellings now work, and the mechanism is worth stating because it is what
makes the change safe. The helpers were **already** written against a FieldFile:
`create_excel_file_from_dfs` ends in `self.save(name, content, save=False)`, and
`save(name, content, save=…)` is the FieldFile API, not the Field API. They were
never field methods that someone mis-called; they were FieldFile methods living
on the wrong class. So `XLSXFieldFile` binds *the same function objects* rather
than reimplementing them, and the ~30 unbound call sites across the estate keep
resolving to identical bytecode. Django does exactly this for `ImageField`
(`attr_class = ImageFieldFile`); the descriptor's own comment invites it.

## The second trap was in the same line of the declaration

`XLSXField.max_length = 300` has never done anything. `FileField.__init__` does
`kwargs.setdefault("max_length", 100)` and `Field.__init__` then sets the
*instance* attribute from kwargs, shadowing the class attribute — so every bare
`XLSXField()` has been `varchar(100)`. The proof is in downstream migration
files: they carry no `max_length` kwarg at all, because `FileField.deconstruct()`
deletes it when it equals 100.

What makes it worth fixing rather than documenting is the failure mode.
Over-length names do not raise: `Storage.get_available_name` treats "longer than
`max_length`" as *not available* and walks into its truncate-and-suffix loop, so
the report lands under a name nobody chose and nothing says so. The app that
prompted this had gone the other way in the same commit — from
`FileField(max_length=300)` to a bare `XLSXField()` — quietly narrowing its
report columns from 300 to 100 while looking like it was adopting the richer
field.

## Notes for whoever reads this next

- **13.40 and 13.41 are the "what did the old code get for free" scenarios.**
  Changing `attr_class` changes the class of a value that the framework already
  passes through two typed boundaries: the audit-log payload serializer branches
  on `isinstance(v, FieldFile)`, and `calc_and_save` receives model instances
  over the broker, so the value is pickled. Neither is what the change is *for*,
  and both would have failed silently — the audit rows would simply stop
  carrying file fields, and the pickle break would appear only in a worker.
- **`attr_class` is not a total guarantee for the bound form.** Django's
  `FileDescriptor.__get__` deliberately does not re-wrap a value that is already
  a `FieldFile` (`files.py`, the `not hasattr(file, "field")` and
  `instance is not file.instance` branches). A plain `FieldFile` constructed by
  hand and assigned onto an instance stays plain, and the bound call still fails
  there. The unbound form remains the one that always works, which is why it
  stays the documented convention rather than being deprecated.
- **The max_length half generates migrations downstream, the binding half does
  not.** `attr_class` is not a field kwarg and not part of `deconstruct()` —
  `makemigrations --check` reports no changes. `max_length` is, so every app
  using either field gets one `AlterField` per report column on its next
  `makemigrations`. `lex_migrate` runs `makemigrations` by default, so the
  widening lands on deploy; an app deploying with `--no-makemigrations` would
  have Django believing 300 against a `varchar(100)` column, which converts a
  silent truncation into a `DataError`. Flagged in the release entry rather than
  guarded in code — no lex-app model uses either field, so nothing ships here.
- **13.42/13.44/13.45 were checked red.** Reverting only the `kwargs.setdefault`
  lines fails exactly those three (`100 != 300`, and the long path comes back
  truncated) while the four binding scenarios stay green — the two halves of the
  batch gate independently.
