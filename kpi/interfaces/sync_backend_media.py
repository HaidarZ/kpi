# coding: utf-8
from kpi.exceptions import AbstractMethodError, AbstractPropertyError


class SyncBackendMediaInterface:
    """
    This interface defines required properties and methods
    of objects passed to deployment back-end class on media synchronization.

    """

    @property
    def backend_data_value(self):
        raise AbstractPropertyError

    @property
    def backend_uniqid(self):
        raise AbstractPropertyError

    def delete(self, **kwargs):
        raise AbstractMethodError

    @property
    def deleted_at(self):
        raise AbstractPropertyError

    @property
    def filename(self):
        raise AbstractPropertyError

    @property
    def hash(self):
        raise AbstractPropertyError

    @property
    def is_remote_url(self):
        raise AbstractPropertyError

    @property
    def mimetype(self):
        raise AbstractPropertyError