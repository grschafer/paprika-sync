from django.contrib.auth import get_user_model
from django.db import models


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PaprikaAccount(BaseModel):
    IMPORT_DEFERRED, IMPORT_INPROGRESS, IMPORT_SUCCESS = 'deferred', 'inprogress', 'success'
    STATUS_CHOICES = (
        (IMPORT_DEFERRED, IMPORT_DEFERRED),
        (IMPORT_INPROGRESS, IMPORT_INPROGRESS),
        (IMPORT_SUCCESS, IMPORT_SUCCESS),
    )
    STATUS_CHOICES_LIST = (IMPORT_DEFERRED, IMPORT_INPROGRESS, IMPORT_SUCCESS)

    user = models.ForeignKey(get_user_model(), related_name='paprika_accounts', on_delete=models.CASCADE)
    username = models.CharField(max_length=150, help_text='Username to login to paprika')
    password = models.CharField(max_length=128, help_text='Password to login to paprika')
    alias = models.CharField(max_length=150, help_text='Name to associate with this account in news feed items (e.g. Alice, Bob)')
    import_status = models.CharField(max_length=150, choices=STATUS_CHOICES, blank=True, help_text='Status of importing all recipes')

    def __str__(self):
        return '{} ({})'.format(self.alias, self.username)


class Recipe(BaseModel):
    paprika_account = models.ForeignKey('core.PaprikaAccount', related_name='recipes', on_delete=models.CASCADE)
    uid = models.CharField(max_length=200)
    hash = models.CharField(max_length=200)
    photo_hash = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    # TODO: do these need to be nullable?
    image_url = models.URLField(max_length=200)

    def __str__(self):
        return self.name


class NewsItem(BaseModel):
    def __str__(self):
        pass
