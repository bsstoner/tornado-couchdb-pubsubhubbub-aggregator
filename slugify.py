import random, string
import re
import unicodedata
from htmlentitydefs import name2codepoint

def unique_slugify(s, entities=True, decimal=True, hexadecimal=True,
   instance=None, slug_field='slug', filter_dict=None, content_object=False,
   delimiter='_',site=False):
    """ 
    Based on Django snippet 369:  http://www.djangosnippets.org/snippets/369/
    Modified to use underscores instead of hyphens....
    Also added owner_instance, when passed, slug only has to be unique to owner
    
    **BS added content_type variable, if set to true instance slug will be made unique for
    that content_object only.  Can have have duplicate slugs in system as long as they are owned by different content_objects
    """
    #s = smart_unicode(s)

    #character entity reference
    if entities:
        s = re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)

    #decimal character reference
    if decimal:
        try:
            s = re.sub('&#(\d+);', lambda m: unichr(int(m.group(1))), s)
        except:
            pass

    #hexadecimal character reference
    if hexadecimal:
        try:
            s = re.sub('&#x([\da-fA-F]+);', lambda m: unichr(int(m.group(1), 16)), s)
        except:
            pass

    #translate
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')

    #replace unwanted characters
    s = re.sub(r'[^-a-z0-9]+', delimiter, s.lower())

    # replace hyphens with underscores....
    s = re.sub('-', delimiter, s)

    #remove redundant -
    s = re.sub(delimiter + '{2,}', delimiter, s).strip('_')

    return s

#===============================================================================
#    if instance:
#        def get_query():
#            query = instance.__class__.objects.filter(**{slug_field: slug})
#            if filter_dict:
#                query = query.filter(**filter_dict)
#            if content_object:
#                query = query.filter(**{'content_type':instance.content_type,'object_id':instance.object_id})
#            if site:
#                query = query.filter(**{'site__domain__slug':instance.site.domain.slug})
#            if instance.pk:
#                query = query.exclude(pk=instance.pk)
#                print query 
#            return query
#        counter = 1
#        while get_query():
#            slug = "%s%s" % (s, counter)
#            counter += 1
#===============================================================================
