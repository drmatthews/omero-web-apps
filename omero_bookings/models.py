import hashlib
from django.utils.encoding import smart_str
from django.db import models

def get_hexdigest(algorithm, salt, raw_password):
    """
    Returns a string of the hexdigest of the given plaintext password and salt
    using the given algorithm ('md5', 'sha1' or 'crypt').
    """
    raw_password, salt = smart_str(raw_password), smart_str(salt)
    if algorithm == 'crypt':
        try:
            import crypt
        except ImportError:
            raise ValueError('"crypt" password algorithm not supported in this environment')
        return crypt.crypt(raw_password, salt)

    if algorithm == 'md5':
        return hashlib.md5(salt + raw_password).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(salt + raw_password).hexdigest()
    raise ValueError("Got unknown password algorithm type in password.")

class AccountRequest(models.Model):

    omename = models.CharField(max_length=30)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=75)
    password = models.CharField(max_length=200)
    institution = models.CharField(max_length=100)
    default_group = models.CharField(max_length=100)
    other_groups = models.CharField(max_length=100)

    def set_password(self, raw_password):
        import random
        algo = 'sha1'
        salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
        hsh = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)
        
    def get_fullname(self):
        return self.first_name + ' ' + self.middle_name + ' ' + self.last_name
        
class Microscope(models.Model):
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    location = models.CharField(default=101,max_length=200)
    rate = models.IntegerField(default=0)

    @property
    def is_active(self):
        return bool(self.active)    
        
    def __unicode__(self):              # __str__ on Python 3
        return self.name
        
class Sample(models.Model):
    description = models.CharField(max_length=200)
    
    def __unicode__(self):              # __str__ on Python 3
        return self.description
    
class MicroscopeBooking(models.Model):
    microscope = models.ManyToManyField(Microscope)
    user_id = models.IntegerField()
    booking_date = models.DateTimeField('booking date')
    
class TrainingRequest(models.Model):
    instrument = models.ManyToManyField(Microscope)
    sample = models.ManyToManyField(Sample)
    marker = models.CharField(max_length=200)
    
