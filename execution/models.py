from django.db import models
from django.db.models.deletion import CASCADE

# Create your models here.


class AuditableMixin(object):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Order(models.Model, AuditableMixin):
    pass


class Fill(models.Model, AuditableMixin):
    order = models.ForeignKey(Order, on_delete=CASCADE)
