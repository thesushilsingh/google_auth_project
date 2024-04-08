from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.


class Shopify_data_model(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, unique=False)
    domain = models.CharField(max_length=100)
    token = models.CharField(max_length=100)
    last_update_timestamp = models.DateTimeField(null=True)

    def __str__(self):
        return self.name


class Shopify_order_model(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100, null=True)
    email = models.EmailField(null=True)
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    order_id = models.BigIntegerField(null=True)
    last_updated = models.DateTimeField(null=True)

    def __str__(self):
        return self.name


class Shopify_product_model(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # order = models.ForeignKey(Shopify_order_model, on_delete=models.CASCADE, null = True)
    product_id = models.BigIntegerField(null=True)
    name = models.CharField(max_length=100, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(max_length=100, null=True)
    updated_at = models.DateTimeField(null=True)

    def __str__(self):
        return self.name
