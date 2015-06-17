from django.db.models import signals, FieldDoesNotExist, Manager


class ESMeta(object):
    pass


def add_elasticsearch_manager(sender, *args, **kwargs):
    from django.conf import settings

    cls = sender
    database = settings.DATABASES[cls.objects.db]
    if 'elasticsearch' in database['ENGINE']:
        if cls._meta.abstract:
            return

        if getattr(cls, 'es', None) is None:
            # Create the default manager, if needed.
            try:
                cls._meta.get_field('es')
                raise ValueError("Model %s must specify a custom Manager, because it has a field named 'objects'" % cls.__name__)
            except FieldDoesNotExist:
                pass
            setattr(cls, 'es', Manager())

            es_meta = getattr(cls, "ESMeta", ESMeta).__dict__.copy()
            # setattr(cls, "_meta", ESMeta())
            for attr in es_meta:
                if attr.startswith("_"):
                    continue
                setattr(cls._meta, attr, es_meta[attr])


signals.class_prepared.connect(add_elasticsearch_manager)