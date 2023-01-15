from django.db import models
from django.conf import settings

from django.urls import reverse


class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='images/', blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("category_detail", kwargs={"pk": self.pk})


class Item(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.FloatField()
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    discount = models.FloatField(default=0, blank=True, null=True)
    category = models.ManyToManyField(Category)
    reviews = models.ManyToManyField('Review', blank=True)
    technical = models.TextField(
        blank=True, null=True, default='this product has no technical specifications')

    def __str__(self):
        return self.title

    def price_format(self):
        return f'${self.price}'

    @property
    def amount(self):
        if self.discount:
            return self.price - self.price * self.discount / 100
        return self.price

    def summary(self):
        return self.description[:100]


class Review(models.Model):
    items = models.ForeignKey(Item, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    rating = models.IntegerField()
    review = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.review

    def get_absolute_url(self):
        return reverse("Review_detail", kwargs={"pk": self.pk})


class OrderItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    isOrdered = models.BooleanField(default=False)


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    item = models.ManyToManyField(OrderItem)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Order_detail", kwargs={"pk": self.pk})
