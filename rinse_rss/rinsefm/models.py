from django.db import models


class Show(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField(unique=True)

    def __str__(self):
        return self.name


class PodcastEpisode(models.Model):
    title = models.CharField(max_length=200)
    broadcast_date = models.DateTimeField()
    audio_url = models.URLField(unique=True)
    audio_content_length = models.PositiveSmallIntegerField()
    audio_content_type = models.CharField(max_length=200)
    show = models.ForeignKey(Show)

    def __str__(self):
        return '%s (%s)' % (self.title, self.broadcast_date)
