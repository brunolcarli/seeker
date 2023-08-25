from django.db import models


class FoundURL(models.Model):
    link = models.TextField(blank=False, null=False, unique=True)
    viewed = models.BooleanField(default=False)
    status_code = models.IntegerField(null=True) 


class RawText(models.Model):
    content = models.TextField(blank=False, null=False)
    char_count = models.IntegerField(null=False)
    word_count = models.IntegerField(null=False)
    sentence_count = models.IntegerField(null=False)
    raw_url = models.TextField(blank=False, null=False)
    url_reference = models.ForeignKey(FoundURL, null=True, on_delete=models.CASCADE)


class ProcText(models.Model):
    content = models.TextField(blank=False, null=False)
    char_count = models.IntegerField(null=False)
    word_count = models.IntegerField(null=False)
    sentence_count = models.IntegerField(null=False)
    tokenized = models.BinaryField(null=False)
    sentences = models.BinaryField(null=False)
    raw_url = models.TextField(blank=False, null=False)
    raw_text_reference = models.ForeignKey(RawText, null=True, on_delete=models.CASCADE)

