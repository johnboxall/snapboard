# From the excellent resource http://www.verdjn.com

import os
import cStringIO
from PIL import Image as PILImage
from django.db import models
from django import forms
from django.dispatch import dispatcher
from django.db.models import signals
from django.conf import settings

# PhotoField is compatible with ImageField from either verdjnlib or Django
# One of the following two lines should be commented out
#from verdjnlib.fields import ImageField
from django.db.models import ImageField


FIT = 0
CROP = 1
DEFAULT_MODE = FIT
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480


class PhotoField(ImageField):

    def __init__(self, verbose_name=None, name=None, width_field=None, height_field=None, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, mode=DEFAULT_MODE, quality=None, parent_pk=None, **kwargs):
        self.width_field, self.height_field = width_field, height_field
        super(PhotoField, self).__init__(verbose_name, name, width_field, height_field, **kwargs)
        self.width, self.height, self.mode, self.quality = width, height, mode, quality
        self.parent_pk = parent_pk or "UNDEFINED"

    def get_internal_type(self):
        return 'ImageField'

    def _update_parent_pk(self, instance=None):
        self.parent_pk = instance._get_pk_val()

    def contribute_to_class(self, cls, name):
        super(PhotoField, self).contribute_to_class(cls, name)
        # Add get_FIELD_content_type method
        setattr(cls, 'get_%s_content_type' % self.name, lambda instance: "image/jpeg")
        dispatcher.connect(self._update_parent_pk, signals.post_save, sender=cls)

    def get_content_type(self):
        return "image/jpeg"

    def save_file(self, new_data, new_object, original_object, change, rel):
        field_names = self.get_manipulator_field_names('')
        upload_field_name = field_names[0]
        filename = '%s-%s.jpg' % (self.parent_pk, self.get_attname())
        # If there is no DeleteCheckbox or the DeleteCheckbox was not checked
        if len(field_names) < 3 or not new_data.get(field_names[2], False):
            if new_data.get(upload_field_name, False):
                if rel:
                    new_data[upload_field_name][0]["filename"] = filename 
                    new_data[upload_field_name][0]["content"] = PhotoField.resize(new_data[upload_field_name][0]["content"], self.width, self.height, self.mode, self.quality)
                else:
                    new_data[upload_field_name]["filename"] = filename
                    new_data[upload_field_name]["content"] = PhotoField.resize(new_data[upload_field_name]["content"], self.width, self.height, self.mode, self.quality)
                # If file exists, delete it
                filepath = os.path.join(settings.MEDIA_ROOT, self.upload_to, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
        super(PhotoField, self).save_file(new_data, new_object, original_object, change, rel)

    def resize(cls, data, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, mode=DEFAULT_MODE, quality=None):
        """Resize an image given as the string data to fit the bounding box
           (width, height). Mode may either be FIT, in which case the image is 
           shrunk to fit completely within the bounding box (the new image may 
           be smaller than the bounding box), or CROP, in which case the image 
           is cropped to the aspect ratio of the bounding box, and then resized 
           to fit (the new image will be the same size as the bounding box)."""
        data_file = cStringIO.StringIO(data)
        pil_obj = PILImage.open(data_file)
        if pil_obj.mode != 'RGB':
            pil_obj = pil_obj.convert('RGB')

        if mode == FIT:
            # Reduce the image's size by using the PIL's thumbnail method, which
            # preserves the aspect ratio of the original image, but does not
            # guarantee that the image will be (scale_width x scale_height) in
            # size. (It will extend to at least one of those dimensions, however.)
            pil_obj.thumbnail((int(width), int(height)), PILImage.ANTIALIAS)

        elif mode == CROP:
            x, y = pil_obj.size

            # If the main image is larger in both dimensions than the desired
            # thumbnail (this is the normal situation,) crop the image to the
            # aspect ratio of the thumbnail, centred on the main image, and
            # reduce the cropped image to thumbnail-size.
            if x >= width and y >= height:
                aspect = float(width) / float(height)
                crop_width = min(int(aspect*y), x)
                crop_height = min(int(float(x)/aspect), y)
                crop_point_x = (x-crop_width)/2
                crop_point_y = (y-crop_height)/2
                pil_obj = pil_obj.crop((crop_point_x, crop_point_y, crop_point_x+crop_width, crop_point_y+crop_height))
                pil_obj.thumbnail((width, height), PILImage.ANTIALIAS)

            # Otherwise, if either the width or height of the main image is
            # less than the thumbnail size, crop the image to the largest
            # rectangle which fits inside of the thumbnail size. (This will
            # be the image's complete extent in at least one dimension.) In
            # this case, we do not reduce the size of the cropped image.
            else:
                crop_width = min(width, x)
                crop_height = min(height, y)
                crop_point_x = (x-crop_width)/2
                crop_point_y = (y-crop_height)/2
                pil_obj = pil_obj.crop((crop_point_x, crop_point_y, crop_point_x+crop_width, crop_point_y+crop_height))

        out_file = cStringIO.StringIO()
        if quality:
            pil_obj.save(out_file, 'JPEG', quality=quality)
        else:
            pil_obj.save(out_file, 'JPEG')
        out_file.reset()
        return out_file.read()

    resize=classmethod(resize)
# vim: ai ts=4 sts=4 et sw=4
