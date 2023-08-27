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


class TextMetadata(models.Model):
    content = models.TextField(blank=False, null=False)
    bigrams = models.BinaryField(null=False)
    trigrams = models.BinaryField(null=False)
    frequency = models.BinaryField(null=False)
    bigrams_freq = models.BinaryField(null=False)
    trigrams_freq = models.BinaryField(null=False)
    part_of_speech = models.BinaryField(null=False)
    text_offense = models.BinaryField(null=False)
    proc_text_reference = models.ForeignKey(ProcText, on_delete=models.CASCADE)
