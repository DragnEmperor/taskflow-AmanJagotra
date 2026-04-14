from rest_framework import serializers


class MetaSerializer(serializers.Serializer):
    """Extended version of `rest_frameowrk.serializers.Serializer` with some added
    capabilities and checks.
    """

    _list_error = "The fields specified must be a list or tuple. Got {type}."
    _missing_field = "The field '{field_name}' does not exist on '{serializer_class}'"

    @classmethod
    def get_meta_attr(cls, field_name: str, default=None):
        """Get specified fields from Meta class"""
        return getattr(getattr(cls, "Meta", None), field_name, default)

    @classmethod
    def many_init(cls, *args, **kwargs):
        list_kwargs = {
            "allow_empty": kwargs.pop("allow_empty", None),
            "max_length": kwargs.pop("max_length", None),
            "child": cls(*args, **kwargs),
        }
        object_only_fields = cls.get_meta_attr("object_only_fields", default=[])
        list_kwargs["child"].validate_fields(object_only_fields)
        for field_name in object_only_fields:
            if list_kwargs["child"].fields[field_name].read_only:
                list_kwargs["child"].fields.pop(field_name)
                continue
            list_kwargs["child"].fields[field_name].write_only = True
        meta = getattr(cls, "Meta", None)
        list_class = getattr(meta, "list_serializer_class", serializers.ListSerializer)
        return list_class(*args, **kwargs, **list_kwargs)

    def validate_fields(self, custom_fields):
        if not isinstance(custom_fields, list | tuple):
            raise TypeError(self._list_error.format(type=type(custom_fields).__name__))
        for field_name in custom_fields:
            if field_name not in self.fields:
                raise AssertionError(
                    self._missing_field.format(field_name=field_name, serializer_class=self.__class__.__name__),
                )
