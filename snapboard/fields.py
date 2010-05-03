from django.db import models
from django.db.models.signals import post_save
from django.dispatch import Signal


class SignalFieldMixin(object):
    """
    If the model instance contains this field is while this field is dirty,
    fires a signal providing the state of the model when it was first made.
    
    """
    def value_from_object(self, obj):
        if not hasattr(obj, "_state"):
            obj._state = {}
        obj._state[self.name] = obj.__dict__.get(self.name)
        return super(SignalFieldMixin, self).value_from_object(obj)
    
    def contribute_to_class(self, cls, name):
        super(SignalFieldMixin, self).contribute_to_class(cls, name)
        post_save.connect(self.updated, sender=cls)
        
    def updated(self, instance, force=False, *args, **kwargs):
        if hasattr(instance, "_state"):
            fields_updated.send(sender=instance, state=instance._state)
            # Prevent multiple signals, reset state.
            del instance._state


class SignalSlugField(SignalFieldMixin, models.SlugField):
    pass

fields_updated = Signal(providing_args=["state"])