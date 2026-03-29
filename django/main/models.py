from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
import secrets


class User(AbstractUser):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    profile_slug = models.SlugField(unique=True, blank=True)

    YEAR_CHOICES = [
        ('1', '1st year'),
        ('2', '2nd year'),
        ('3', '3rd year'),
        ('4', '4th year'),]

    SCHOOL_CHOICES = [
        ('engineering', 'School of Engineering and Applied Science'),
        ('cas', 'College of Arts and Sciences'),
        ('commerce', 'McIntire School of Commerce'),
        ('architecture', 'School of Architecture'),
        ('education', 'School of Education and Human Development'),
        ('nursing', 'School of Nursing'),
        ('batten', 'Batten School of Leadership and Public Policy'),
    ]

    is_user_admin = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    age = models.PositiveIntegerField(default=0)
    birthday = models.DateField(null=True, blank=True)
    year = models.CharField(max_length = 1, choices = YEAR_CHOICES, blank=True, null=True)
    school = models.CharField(max_length = 50, choices = SCHOOL_CHOICES, blank=True, null=True)

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
    executive_code = models.CharField(max_length=8, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.executive_code:
            self.executive_code = secrets.token_hex(4)
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

#basic event setup - to be edited
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=200)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='events')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Forum(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='forums')

    def __str__(self):
        return f"Forum for {self.club.name}"

class ForumThread(models.Model):
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='threads')
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_threads', blank=True)

    def __str__(self):
        return self.title

class ForumReply(models.Model):
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_replies', blank=True)

    def __str__(self):
        return f"Reply by {self.author} on {self.thread}"

# ──────────────────────────────────────────────
# MESSAGING MODELS
# ──────────────────────────────────────────────

class DirectMessage(models.Model):
    """A private message between two users."""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_dms')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_dms')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"DM from {self.sender} to {self.recipient}"
    
    
