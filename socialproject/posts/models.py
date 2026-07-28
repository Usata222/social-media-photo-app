from django.db import models
from django.conf import settings
from django.utils.text import slugify
# Create your models here.


class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/%y/%m/%d')
    caption = models.TextField(blank=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    created = models.DateField(auto_now_add=True)
    liked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='posts_liked', blank=True)

    class Meta:
        ordering = ('-created', '-id')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def like_count(self):
        return self.liked_by.count()

    @property
    def comment_count(self):
        return self.comments.count()


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='comments', null=True, blank=True)
    body = models.CharField(max_length=100)
    # NOTE: this was previously `auto_now=True`, which rewrites the timestamp
    # on every save (including edits). Changed to `auto_now_add` so the
    # original post time is preserved, with a separate `updated` field below.
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    posted_by = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ('created',)

    def __str__(self):
        return self.body

    @property
    def is_edited(self):
        return self.updated and self.created and (
            self.updated - self.created).total_seconds() > 1


class Bookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='bookmarks')
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='bookmarked_by')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'], name='unique_bookmark')
        ]

    def __str__(self):
        return f'{self.user} bookmarked {self.post}'
