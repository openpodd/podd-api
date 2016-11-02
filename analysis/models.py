from django.db import models

# Create your models here.
class Word(models.Model):

    en_word = models.TextField()
    th_word = models.TextField(null=True)

    def __unicode__(self):
        return self.en_word



'''

class AnimalSickAnalysis(models.Model):

    word = models.TextField()
    language = models.CharField(max_length=100)
    eng_word = models.TextField()

    def __unicode__(self):
        return self.word

'''