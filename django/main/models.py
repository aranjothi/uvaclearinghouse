from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify


class User(AbstractUser):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    profile_slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.profile_slug:
            self.profile_slug = slugify(self.username)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Club(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Membership(models.Model):
    EXECUTIVE = 'executive'
    MEMBER = 'member'
    ROLE_CHOICES = [
        (EXECUTIVE, 'Executive'),
        (MEMBER, 'General Member'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=MEMBER)

    class Meta:
        unique_together = ('user', 'club')

    def __str__(self):
        return f"{self.user} - {self.club} ({self.role})"
