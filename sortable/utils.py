"""Sortable Xblock Utils"""

def _(text):
    """no-op function to scrape strings for i18n"""
    return text


def ngettext_fallback(text_singular, text_plural, number):
    """ Dummy `ngettext` replacement to make string extraction tools scrape strings marked for translation """
    if number == 1:
        return text_singular
    return text_plural


class DummyTranslationService(object):
    """
    Dummy drop-in replacement for i18n XBlock service
    """
    gettext = staticmethod(_)
    ngettext = staticmethod(ngettext_fallback)
