from django.db.models import Model


# Mixin to be added to every model, that may cause need to update any calculated models
class DependencyAnalysisMixin(Model):
    """
    Mixin to be added to every model that may cause the need to update any calculated models.

    Attributes
    ----------
    do_cascading_updates : bool
        Set this field to true if, upon updating this entry, not only the entries
        defined in 'directly_dependent_entries' should be considered for updating,
        but also the entries any of those entries depend on.
    """
    # Set this field to true, if, upon updating this entry, not only the entries
    # defined in 'directly_dependent_entries' should be considered for updating,
    # but also the entries any of those entries depend on
    do_cascading_updates = False

    class Meta:
        abstract = True

    # Override this method to define all entries, from which some calculated model directly
    # accesses this entry (typically entries, that have foreign keys to this one)
    # Should return a set of entries
    def directly_dependent_entries(self):
        """
        Override this method to define all entries from which some calculated model directly
        accesses this entry (typically entries that have foreign keys to this one).

        Returns
        -------
        set
            A set of entries.
        """
        return {}

    # Returns all entries, that the user requires to be updated whenever this entry is, as keys of a dictionary
    # TODO: Deal with circular dependencies
    def get_dependent_entries(self):
        """
        Returns all entries that the user requires to be updated whenever this entry is, as keys of a dictionary.

        TODO: Deal with circular dependencies.

        Returns
        -------
        dict
            A dictionary of dependent entries.
        """
        dependent_entries = dict.fromkeys(self.directly_dependent_entries())
        if self.do_cascading_updates:
            cascading_dependent_entries_list = list(map(
                lambda entry: entry.get_dependent_entries(),
                list(filter(
                    lambda entry: issubclass(type(entry), DependencyAnalysisMixin),
                    dependent_entries
                ))
            ))

            for dependent_entry_dict in cascading_dependent_entries_list:
                dependent_entries.update(dependent_entry_dict)

        return dependent_entries
