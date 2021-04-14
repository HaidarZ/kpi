# coding: utf-8
import copy
import json
from typing import Union

from bson import json_util
from django.db.models.query import QuerySet
from django.db import transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import PermissionDenied
from rest_framework import serializers
from rest_framework.pagination import _positive_int as positive_int

from kpi.constants import (
    INSTANCE_FORMAT_TYPE_XML,
    INSTANCE_FORMAT_TYPE_JSON,
    PERM_PARTIAL_SUBMISSIONS,
    PERM_VIEW_SUBMISSIONS,
)
from kpi.exceptions import AbstractMethodError
from kpi.interfaces.sync_backend_media import SyncBackendMediaInterface
from kpi.models.asset_file import AssetFile
from kpi.models.paired_data import PairedData
from kpi.utils.jsonbfield_helper import ReplaceValues


class BaseDeploymentBackend:

    INSTANCE_ID_FIELDNAME = '_id'
    STATUS_SYNCED = 'synced'
    STATUS_NOT_SYNCED = 'not-synced'

    def __init__(self, asset):
        self.asset = asset
        # Python-only attribute used by `kpi.views.v2.data.DataViewSet.list()`
        self.current_submissions_count = 0

    @property
    def active(self):
        return self.get_data('active', False)

    @property
    def backend(self):
        return self.get_data('backend', None)

    @property
    def backend_response(self):
        return self.get_data('backend_response', {})

    def calculated_submission_count(self, requesting_user_id, **kwargs):
        raise AbstractMethodError

    def delete(self):
        self.asset._deployment_data.clear()  # noqa

    def get_data(self,
                 dotted_path: str = None,
                 default=None) -> Union[None, int, str, dict]:
        """
        Access `self.asset._deployment_data` and return corresponding value of
        `dotted_path` if it exists. Otherwise, it returns `default`.
        If `dotted_path` is not provided, it returns the whole
        dictionary.
        """
        if not dotted_path:
            # We do not want to return the mutable object whose could be altered
            # later. `self.asset._deployment_data` should never be accessed
            # directly
            return copy.deepcopy(self.asset._deployment_data) # noqa

        value = None
        nested_path = dotted_path.split('.')
        nested_dict = self.asset._deployment_data  # noqa
        for key in nested_path:
            try:
                value = nested_dict[key]
            except KeyError:
                value = None
                break

            nested_dict = value

        return value if value else default

    def get_submission(self, pk, requesting_user_id,
                       format_type=INSTANCE_FORMAT_TYPE_JSON, **kwargs):
        """
        Returns submission if `pk` exists otherwise `None`

        Args:
            pk (int): Submission's primary key
            requesting_user_id (int)
            format_type (str): INSTANCE_FORMAT_TYPE_JSON|INSTANCE_FORMAT_TYPE_XML
            kwargs (dict): Filters to pass to MongoDB. See
                https://docs.mongodb.com/manual/reference/operator/query/

        Returns:
            (dict|str|`None`): Depending on `format_type`, it can return:
                - Mongo JSON representation as a dict
                - Instance's XML as string
                - `None` if doesn't exist
        """

        submissions = list(self.get_submissions(requesting_user_id,
                                                format_type, [int(pk)],
                                                **kwargs))
        try:
            return submissions[0]
        except IndexError:
            pass
        return None

    @property
    def identifier(self):
        return self.get_data('identifier', None)

    @property
    def last_submission_time(self):
        return self._last_submission_time()

    @property
    def mongo_userform_id(self):
        return None

    def remove_from_kc_only_flag(self, *args, **kwargs):
        # TODO: This exists only to support KoBoCAT (see #1161) and should be
        # removed, along with all places where it is called, once we remove
        # KoBoCAT's ability to assign permissions (kobotoolbox/kobocat#642)

        # Do nothing, without complaint, so that callers don't have to worry
        # about whether the back end is KoBoCAT or something else
        pass

    def save_to_db(self, updates: dict):
        """
        Persist values from deployment data into the DB.
        `updates` is a dictionary of properties to update.
        E.g: `{"active": True, "status": "not-synced"}`
        """
        # Avoid circular imports
        # use `self.asset.__class__` instead of `from kpi.models import Asset`
        now = timezone.now()
        with transaction.atomic():
            self.asset.__class__.objects.select_for_update() \
                .filter(id=self.asset.pk).update(
                _deployment_data=ReplaceValues(
                    '_deployment_data',
                    updates=updates,
                ),
                date_modified=now,
            )
        self.store_data(updates)
        self.asset.date_modified = now

    def set_asset_uid(self, **kwargs) -> bool:
        raise AbstractMethodError

    def set_status(self, status):
        self.save_to_db({'status': status})

    @property
    def status(self):
        return self.get_data('status')

    def store_data(self, vals=None):
        self.asset._deployment_data.update(vals)  # noqa

    @property
    def submission_count(self):
        return self._submission_count()

    def remove_from_kc_only_flag(self, *args, **kwargs):
        # TODO: This exists only to support KoBoCAT (see #1161) and should be
        # removed, along with all places where it is called, once we remove
        # KoBoCAT's ability to assign permissions (kobotoolbox/kobocat#642)

        # Do nothing, without complaint, so that callers don't have to worry
        # about whether the back end is KoBoCAT or something else
        pass

    def sync_media_files(self, file_type: str = AssetFile.FORM_MEDIA):
        queryset = self._get_metadata_queryset(file_type=file_type)
        for obj in queryset:
            assert issubclass(obj.__class__, SyncBackendMediaInterface)

    def validate_submission_list_params(
        self,
        requesting_user_id,
        format_type=INSTANCE_FORMAT_TYPE_JSON,
        validate_count=False,
        **kwargs
    ):
        """
        Ensure types of query and each param.

        Args:
            requesting_user_id (int)
            format_type (str): INSTANCE_FORMAT_TYPE_JSON|INSTANCE_FORMAT_TYPE_XML
            validate_count (bool): If `True`, ignores `start`, `limit`, `fields`
            & `sort`
            kwargs (dict): Can contain
                - start
                - limit
                - sort
                - fields
                - query
                - instance_ids


        Returns:
            dict
        """

        if 'count' in kwargs:
            raise serializers.ValidationError(
                {
                    'count': _(
                        'This param is not implemented. Use `count` property '
                        'of the response instead.'
                    )
                }
            )

        if validate_count is False and format_type == INSTANCE_FORMAT_TYPE_XML:
            if 'sort' in kwargs:
                # FIXME. Use Mongo to sort data and ask PostgreSQL to follow the order  # noqa
                # See. https://stackoverflow.com/a/867578
                raise serializers.ValidationError({
                    'sort': _('This param is not supported in `XML` format')
                })

            if 'fields' in kwargs:
                raise serializers.ValidationError({
                    'fields': _('This is not supported in `XML` format')
                })

        start = kwargs.get('start', 0)
        limit = kwargs.get('limit')
        sort = kwargs.get('sort', {})
        fields = kwargs.get('fields', [])
        query = kwargs.get('query', {})
        instance_ids = kwargs.get('instance_ids', [])

        # I've copied these `ValidationError` messages verbatim from DRF where
        # possible. TODO: Should this validation be in (or called directly by)
        # the view code? Does DRF have a validator for GET params?

        if isinstance(query, str):
            try:
                query = json.loads(query, object_hook=json_util.object_hook)
            except ValueError:
                raise serializers.ValidationError(
                    {'query': _('Value must be valid JSON.')}
                )

        if not isinstance(instance_ids, list):
            raise serializers.ValidationError(
                {'instance_ids': _('Value must be a list.')}
            )

        # This error should not be returned as `ValidationError` to user.
        # We want to return a 500.
        try:
            partial_perm = kwargs.pop('partial_perm', PERM_VIEW_SUBMISSIONS)
            permission_filters = self.asset.get_filters_for_partial_perm(
                requesting_user_id, perm=partial_perm)
        except ValueError:
            raise ValueError(_('Invalid `requesting_user_id` param'))

        if validate_count:
            return {
                'query': query,
                'instance_ids': instance_ids,
                'permission_filters': permission_filters
            }

        if isinstance(sort, str):
            try:
                sort = json.loads(sort, object_hook=json_util.object_hook)
            except ValueError:
                raise serializers.ValidationError(
                    {'sort': _('Value must be valid JSON.')}
                )

        try:
            start = positive_int(start)
        except ValueError:
            raise serializers.ValidationError(
                {'start': _('A positive integer is required.')}
            )
        try:
            if limit is not None:
                limit = positive_int(limit, strict=True)
        except ValueError:
            raise serializers.ValidationError(
                {'limit': _('A positive integer is required.')}
            )

        if isinstance(fields, str):
            try:
                fields = json.loads(fields, object_hook=json_util.object_hook)
            except ValueError:
                raise serializers.ValidationError(
                    {'fields': _('Value must be valid JSON.')}
                )

        params = {
            'query': query,
            'start': start,
            'fields': fields,
            'sort': sort,
            'instance_ids': instance_ids,
            'permission_filters': permission_filters
        }

        if limit:
            params['limit'] = limit

        return params

    def validate_write_access_with_partial_perms(self,
                                                 user: 'auth.User',
                                                 perm: str,
                                                 instance_ids: list):
        """
        Validate whether `user` is allowed to perform write actions on
        submissions with the permission `perm`.
        It raises a `PermissionDenied` error if they cannot.

        No validation is made whether `user` is granted with other permissions
        than 'partial_submission' permission.
        """
        if PERM_PARTIAL_SUBMISSIONS not in self.asset.get_perms(user):
            return

        results = self.get_submissions(
            requesting_user_id=user.pk,
            format_type=INSTANCE_FORMAT_TYPE_JSON,
            partial_perm=perm,
            fields=[self.INSTANCE_ID_FIELDNAME],
            instance_ids=instance_ids,
        )
        allowed_instance_ids = [r[self.INSTANCE_ID_FIELDNAME] for r in results]

        if sorted(allowed_instance_ids) != sorted(instance_ids):
            raise PermissionDenied

    @property
    def version(self):
        raise NotImplementedError('Use `asset.deployment.version_id`')

    @property
    def version_id(self):
        return self.get_data('version')

    def _get_metadata_queryset(self, file_type: str) -> Union[QuerySet, list]:
        if file_type == AssetFile.FORM_MEDIA:
            # Order by `date_deleted` to process deleted files first in case
            # two entries contain the same file but one is flagged as deleted
            return self.asset.asset_files.filter(
                file_type=AssetFile.FORM_MEDIA
            ).order_by('date_deleted')
        else:
            queryset = PairedData.objects(self.asset).values()
            return queryset
