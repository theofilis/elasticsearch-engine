import uuid

import django
from django.db import models
from django.core import exceptions
from django.db.models import CharField
from django.db.models.fields import AutoField as DJAutoField


__all__ = ["EmbeddedModel"]
__doc__ = "ES special fields"


class EmbeddedModel(models.Model):
    _embedded_in = None

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.pk = str(uuid.uuid4())
        if self._embedded_in is None:
            raise RuntimeError("Invalid save")
        self._embedded_in.save()

    def serialize(self):
        if self.pk is None:
            self.pk = "TODO"
            self.id = self.pk
        result = {'_app': self._meta.app_label,
                  '_model': self._meta.module_name,
                  '_id': self.pk}
        for field in self._meta.fields:
            result[field.attname] = getattr(self, field.attname)
        return result


class ElasticField(CharField):
    def __init__(self, *args, **kwargs):
        self.doc_type = kwargs.pop("doc_type", None)

        # This field stores the document id and has to be unique
        kwargs["unique"] = True

        # Let's force the field as db_index so we can get its value faster.
        kwargs["db_index"] = True
        kwargs["max_length"] = 255

        super(ElasticField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(ElasticField, self).contribute_to_class(cls, name)

        index = cls._meta.db_table
        doc_type = self.doc_type
        att_id_name = "_%s_id" % name
        att_cache_name = "_%s_cache" % name
        att_val_name = "_%s_val" % name

        def _get(self):
            """
            self is the model instance not the field instance
            """
            from django.db import connections

            elst = connections[self._meta.elst_connection]
            if not hasattr(self, att_cache_name) and not getattr(self, att_val_name, None) and getattr(self,
                                                                                                       att_id_name,
                                                                                                       None):
                val = elst.get(index, doc_type, id=getattr(self, att_id_name)).get("_source", None)
                setattr(self, att_cache_name, val)
                setattr(self, att_val_name, val)
            return getattr(self, att_val_name, None)

        def _set(self, val):
            """
            self is the model instance not the field instance
            """
            if isinstance(val, basestring) and not hasattr(self, att_id_name):
                setattr(self, att_id_name, val)
            else:
                setattr(self, att_val_name, val or None)

        setattr(cls, self.attname, property(_get, _set))

    def pre_save(self, model_instance, add):
        from django.db import connections

        elst = connections[model_instance._meta.elst_connection]

        id = getattr(model_instance, "_%s_id" % self.attname, None)
        value = getattr(model_instance, "_%s_val" % self.attname, None)
        index = model_instance._meta.db_table
        doc_type = self.doc_type

        if value == getattr(model_instance, "_%s_cache" % self.attname, None) and id:
            return id

        if value:
            # elst = ES('http://127.0.0.1:9200/')
            result = elst.index(doc=value, index=index, doc_type=doc_type, id=id or None)
            setattr(model_instance, "_%s_id" % self.attname, result["_id"])
            setattr(model_instance, "_%s_cache" % self.attname, value)
        return getattr(model_instance, "_%s_id" % self.attname, u"")

    def autofield_to_python(self, value):
        if value is None:
            return value
        try:
            return str(value)
        except (TypeError, ValueError):
            raise exceptions.ValidationError(self.error_messages['invalid'])

    def autofield_get_prep_value(self, value):
        if value is None:
            return None
        return unicode(value)


# def pre_init_mongodb_signal(sender, args, **kwargs):
#     if sender._meta.abstract:
#         return
#
#     from django.conf import settings
#
#     database = settings.DATABASES[sender.objects.db]
#     if 'elasticsearch' not in database['ENGINE']:
#         return
#
#     if not hasattr(django, 'MODIFIED') and isinstance(sender._meta.pk, DJAutoField):
#         pk = sender._meta.pk
#         setattr(pk, "to_python", autofield_to_python)
#         setattr(pk, "get_prep_value", autofield_get_prep_value)

