from django.db import models
from django.conf import settings
# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='users/%Y/%m/%d', blank=True)
    bio = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)

    def __str__(self):
        return self.user.username

    @property
    def followers_count(self):
        return self.user.followers.count()

    @property
    def following_count(self):
        return self.user.following.count()


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='following')
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='followers')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'followed'], name='unique_follow')
        ]

    def __str__(self):
        return f'{self.follower} follows {self.followed}'


class Notification(models.Model):
    LIKE = 'like'
    COMMENT = 'comment'
    FOLLOW = 'follow'
    VERB_CHOICES = [
        (LIKE, 'liked your post'),
        (COMMENT, 'commented on your post'),
        (FOLLOW, 'started following you'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications')
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='sent_notifications')
    verb = models.CharField(max_length=10, choices=VERB_CHOICES)
    # String reference (not a direct import of posts.models.Post) so the
    # users and posts apps don't end up importing each other at module load.
    post = models.ForeignKey(
        'posts.Post', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f'{self.actor} {self.verb} -> {self.recipient}'
