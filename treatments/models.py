from django.db import models

class Treatment(models.Model):
    name = models.CharField(max_length=100)
    duration = models.IntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    pre_care = models.TextField(blank=True)
    post_care = models.TextField(blank=True)
    frequency = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name