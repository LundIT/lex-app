class ObjectsToRecalculateStore:
    """
    A store for objects that need recalculations.

    This class maintains a singleton instance that stores objects
    which need to be recalculated based on their defining fields.

    Attributes
    ----------
    instance : ObjectsToRecalculateStore
        The singleton instance of the store.
    objects_to_recalculate : dict
        A dictionary mapping model IDs to another dictionary that maps
        defining field tuples to objects that need recalculations.
    """
    instance = None

    def __init__(self):
        """
        Initializes the store and sets the singleton instance.
        """
        # calculated_model_id --> (defining_field_tuple --> object_to_recalculate)
        self.objects_to_recalculate = {}
        ObjectsToRecalculateStore.instance = self

    @staticmethod
    def insert(obj):
        """
        Inserts an object into the store for recalculations.

        Parameters
        ----------
        obj : object
            The object to be inserted. It must have `_meta.model_name` and
            `defining_fields` attributes.
        """
        model_id = obj._meta.model_name
        defining_fields = tuple(map(lambda field: obj.__getattribute__(field.name), obj.defining_fields))
        o2r = ObjectsToRecalculateStore.instance.objects_to_recalculate

        if model_id not in o2r:
            o2r[model_id] = {}

        if defining_fields not in o2r[model_id]:
            o2r[model_id][defining_fields] = obj

        ObjectsToRecalculateStore.instance.objects_to_recalculate = o2r

    @staticmethod
    def do_recalculations():
        """
        Performs recalculations on all stored objects and saves them.

        This method iterates over all objects in the store, calls their
        `calculate` and `save` methods, and then clears the store.
        """
        o2r = ObjectsToRecalculateStore.instance.objects_to_recalculate
        for model_id in o2r.keys():
            for def_field_tuple in o2r[model_id].keys():
                obj = o2r[model_id][def_field_tuple]
                obj.calculate()
                obj.save()

        ObjectsToRecalculateStore.instance.objects_to_recalculate = {}
