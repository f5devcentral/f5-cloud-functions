from __future__ import print_function

import os
import boto3
from datetime import datetime, timedelta
from dateutil.parser import parse

REGION = os.getenv('region', 'us-east-1')
# These are two different variables because snapshots resolve the marketplace
# account number to "aws-marketplace" whereas AMIs keep it numeric *facepalm*
SNAPSHOT_ACCOUNTS = os.getenv('snap_accounts', 'aws-marketplace')
AMI_ACCOUNTS = os.getenv('ami_accounts', '679593333241')
ACTUALLY_DO = os.getenv('run', False)
AWS_MARKETPLACE_ID = '679593333241'

if ACTUALLY_DO is not False:
    if ACTUALLY_DO in ['true', 'True', '1', 't', 'y']:
        ACTUALLY_DO = True
    else:
        ACTUALLY_DO = False

Snapshot_Accounts_List = SNAPSHOT_ACCOUNTS.split(';')
AMI_Accounts_List = AMI_ACCOUNTS.split(';')

client = boto3.client('ec2', REGION)


# Grab details on the image and snapshot associated with the image.  If it's
# not shared to any of the accounts in SNAPSHOT_ACCOUNTS or AMI_ACCOUNTS then
# share it with them
def add_perms(image):
    modified_snaps = 0
    modified_images = 0
    modified = False

    # Modify Image
    if image['State'] == 'available':
        launch_permissions = client.describe_image_attribute(
            Attribute='launchPermission',
            ImageId=image['ImageId']
        )
        launch_permissions_users = get_launch_permissions_users(launch_permissions)
        for acct in AMI_Accounts_List:
            if acct not in launch_permissions_users:
                add_launch_permissions(image['ImageId'], acct)
                modified = True
        if modified:
            modified_images += 1
            modified = False

        # Modify Snapshots
        snaps = []
        for storage in image['BlockDeviceMappings']:
            try:
                snaps.append(storage['Ebs']['SnapshotId'])
            except KeyError:
                # not sure why this happens to be honest, it shouldn't
                continue
        for snap in snaps:
            cvp = client.describe_snapshot_attribute(SnapshotId=snap,
                                                     Attribute='createVolumePermission')
            cvp_accts = get_create_volume_users(cvp)
            # for acct in cvp['CreateVolumePermissions']:
            for acct in Snapshot_Accounts_List:
                if acct not in cvp_accts:
                    add_create_volume_permissions(snap, acct)
                    modified = True
            if modified:
                modified_snaps += 1
                modified = False

    return modified_snaps, modified_images


# parse out the user id's from AWS's response
def get_create_volume_users(response):
    accounts = []
    for obj in response['CreateVolumePermissions']:
        accounts.append(obj['UserId'])
    return accounts


# parse out the user id's from AWS's response
def get_launch_permissions_users(response):
    accounts = []
    for obj in response['LaunchPermissions']:
        accounts.append(obj['UserId'])
    return accounts


# Add the launch permission to an account for a given AMI
def add_launch_permissions(image, account):
    if ACTUALLY_DO:
        client.modify_image_attribute(
            Attribute='launchPermission',
            OperationType='add',
            ImageId=image,
            UserIds=[account]
        )
        print("Added permissions to image {} for account {}".format(image, account))
    else:
        print("would add permissions to image {} for account {}".format(image, account))


# Add the create volume permission to an account for a given snapshot
def add_create_volume_permissions(snapshot, account):
    if ACTUALLY_DO:
        if account == 'aws-marketplace':
            account = AWS_MARKETPLACE_ID
        client.modify_snapshot_attribute(
            Attribute='createVolumePermission',
            OperationType='add',
            SnapshotId=snapshot,
            UserIds=[account]
        )
        print("Added permissions to snapshot {} for account {}".format(snapshot, account))
    else:
        print("would add permissions to snapshot {} for account {}".format(snapshot, account))


def lambda_handler(event, context):
    if not ACTUALLY_DO:
        print('No Op enabled, no images or snapshots will actually be modified.')
    modified_image_count = 0
    modified_snapshot_count = 0
    oldest_to_check = datetime.utcnow() - timedelta(hours=1)
    images = client.describe_images(Owners=['self'])['Images']
    if images is not None:
        for image in images:
            creation_date = image['CreationDate']
            date = parse(creation_date).replace(tzinfo=None)
            if date > oldest_to_check:
                print('sharing {} if necessary'.format(image['ImageId']))
                snapshot_count, image_count = add_perms(image)
                modified_image_count += image_count
                modified_snapshot_count += snapshot_count

    if not ACTUALLY_DO:
        print('{} images and {} snapshots would have been modified'.format(
            modified_image_count, modified_snapshot_count))
    else:
        print('{} images and {} snapshots were modified'.format(
            modified_image_count, modified_snapshot_count))
