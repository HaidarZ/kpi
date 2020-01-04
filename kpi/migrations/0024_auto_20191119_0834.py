# Generated by Django 2.2.7 on 2019-11-19 08:34

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields
import kpi.fields.kpi_uid
import kpi.models.asset_file
import kpi.models.import_export_task
import private_storage.fields
import private_storage.storage.s3boto3


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('kpi', '0023_partial_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAssetSubscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', kpi.fields.kpi_uid.KpiUidField(uid_prefix='b')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='usercollectionsubscription',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='usercollectionsubscription',
            name='collection',
        ),
        migrations.RemoveField(
            model_name='usercollectionsubscription',
            name='user',
        ),
        migrations.AlterModelOptions(
            name='asset',
            options={'default_permissions': ('add', 'change', 'delete'), 'ordering': ('-date_modified',), 'permissions': (('view_asset', 'Can view asset'), ('share_asset', "Can change asset's sharing settings"), ('discover_asset', 'Can discover asset in public lists'), ('add_submissions', 'Can submit data to asset'), ('view_submissions', 'Can view submitted data for asset'), ('partial_submissions', 'Can make partial actions on submitted data for asset for specific users'), ('change_submissions', 'Can modify submitted data for asset'), ('delete_submissions', 'Can delete submitted data for asset'), ('share_submissions', "Can change sharing settings for asset's submitted data"), ('validate_submissions', 'Can validate submitted data asset'), ('from_kc_only', 'INTERNAL USE ONLY; DO NOT ASSIGN'))},
        ),
        migrations.AlterField(
            model_name='asset',
            name='_deployment_data',
            field=jsonfield.fields.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='asset',
            name='asset_type',
            field=models.CharField(choices=[('text', 'text'), ('empty', 'empty'), ('question', 'question'), ('block', 'block'), ('survey', 'survey'), ('template', 'template'), ('collection', 'collection')], default='survey', max_length=20),
        ),
        migrations.AlterField(
            model_name='asset',
            name='name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='asset',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='kpi.Asset'),
        ),
        migrations.AlterField(
            model_name='asset',
            name='summary',
            field=jsonfield.fields.JSONField(default=dict, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='uid',
            field=kpi.fields.kpi_uid.KpiUidField(uid_prefix='a'),
        ),
        migrations.AlterField(
            model_name='assetfile',
            name='content',
            field=private_storage.fields.PrivateFileField(max_length=380, storage=private_storage.storage.s3boto3.PrivateS3BotoStorage(), upload_to=kpi.models.asset_file.upload_to),
        ),
        migrations.AlterField(
            model_name='assetfile',
            name='file_type',
            field=models.CharField(choices=[('map_layer', 'map_layer')], max_length=32),
        ),
        migrations.AlterField(
            model_name='assetfile',
            name='uid',
            field=kpi.fields.kpi_uid.KpiUidField(uid_prefix='af'),
        ),
        migrations.AlterField(
            model_name='assetsnapshot',
            name='details',
            field=jsonfield.fields.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='assetsnapshot',
            name='uid',
            field=kpi.fields.kpi_uid.KpiUidField(uid_prefix='s'),
        ),
        migrations.AlterField(
            model_name='assetversion',
            name='_deployment_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='assetversion',
            name='uid',
            field=kpi.fields.kpi_uid.KpiUidField(uid_prefix='v'),
        ),
        migrations.AlterField(
            model_name='exporttask',
            name='result',
            field=private_storage.fields.PrivateFileField(max_length=380, storage=private_storage.storage.s3boto3.PrivateS3BotoStorage(), upload_to=kpi.models.import_export_task.export_upload_to),
        ),
        migrations.AlterField(
            model_name='exporttask',
            name='status',
            field=models.CharField(choices=[('created', 'created'), ('processing', 'processing'), ('error', 'error'), ('complete', 'complete')], default='created', max_length=32),
        ),
        migrations.AlterField(
            model_name='exporttask',
            name='uid',
            field=kpi.fields.kpi_uid.KpiUidField(uid_prefix='e'),
        ),
        migrations.AlterField(
            model_name='importtask',
            name='status',
            field=models.CharField(choices=[('created', 'created'), ('processing', 'processing'), ('error', 'error'), ('complete', 'complete')], default='created', max_length=32),
        ),
        migrations.AlterField(
            model_name='importtask',
            name='uid',
            field=kpi.fields.kpi_uid.KpiUidField(uid_prefix='i'),
        ),
        migrations.AlterField(
            model_name='objectpermission',
            name='deny',
            field=models.BooleanField(default=False, help_text='Blocks inheritance of this permission when set to True'),
        ),
        migrations.AlterField(
            model_name='objectpermission',
            name='uid',
            field=kpi.fields.kpi_uid.KpiUidField(uid_prefix='p'),
        ),
        migrations.AlterField(
            model_name='taguid',
            name='uid',
            field=kpi.fields.kpi_uid.KpiUidField(uid_prefix='t'),
        ),
        migrations.DeleteModel(
            name='Collection',
        ),
        migrations.DeleteModel(
            name='UserCollectionSubscription',
        ),
        migrations.AddField(
            model_name='userassetsubscription',
            name='asset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kpi.Asset'),
        ),
        migrations.AddField(
            model_name='userassetsubscription',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='userassetsubscription',
            unique_together={('asset', 'user')},
        ),
    ]