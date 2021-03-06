from django.db import models


class PodcastEpisode(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    broadcast_date = models.DateTimeField()
    audio_url = models.URLField(unique=True)
    audio_content_length = models.PositiveIntegerField()
    audio_content_type = models.CharField(max_length=200)

    class Meta:
        ordering = ('-broadcast_date',)

    def __str__(self):
        return '%s (%s)' % (self.title, self.broadcast_date)

    def get_absolute_url(self):
        return self.audio_url
