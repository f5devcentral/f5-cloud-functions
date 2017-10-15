from __future__ import print_function

import os
import boto3
from datetime import datetime, timedelta
from dateutil.parser import parse

THRESHOLD = int(os.getenv('threshold_days', 30))
ENABLE_DELETE = os.getenv('enable_delete', False)
REGION = os.getenv('region', 'us-east-1')
LIMIT = int(os.getenv('limit', 400))

if ENABLE_DELETE is not False:
    if ENABLE_DELETE in ['true', 'True', '1', 't', 'y']:
        ENABLE_DELETE = True
    else:
        ENABLE_DELETE = False

client = boto3.client('ec2', REGION)


def check_remove_image(image, threshold_date):
    if exceeds_threshold(image, threshold_date):
        remove_image(image)
        return True
    return False


def remove_image(image):
    # Remove the image
    snaps = []
    for storage in image['BlockDeviceMappings']:
        snaps.append(storage['Ebs']['SnapshotId'])

    print('{} is being deleted'.format(image['ImageId']))
    if ENABLE_DELETE:
        client.deregister_image(ImageId=image['ImageId'])
    for snapshot in snaps:
        print('{} is being deleted'.format(snapshot))
        if ENABLE_DELETE:
            client.delete_snapshot(SnapshotId=snapshot)


def exceeds_threshold(images, threshold_date):
    create_ts = images['CreationDate']
    date = parse(create_ts)
    # Just strip the timezone info, it doesn't have to be super accurate
    # within 24 hours is good enough
    date = date.replace(tzinfo=None)

    return date < threshold_date


def lambda_handler(event, context):
    if not ENABLE_DELETE:
        print('No Op enabled, no images will actually be deleted.')
    oldest_allowed = datetime.utcnow() - timedelta(days=THRESHOLD)
    print('Pruning AMIs older than {}'.format(str(oldest_allowed)))
    deleted_count = 0

    images = client.describe_images(Owners=['self'])['Images']
    if images is not None:
        for image in images:
            if ENABLE_DELETE and deleted_count >= LIMIT:
                # Only stop at the limit if this is NOT a no op
                break
            keep_tag_found = False
            if 'Tags' in image:
                for tag in image['Tags']:
                    if tag['Key'] == 'keep':
                        keep_tag_found = True
                        break
                if keep_tag_found:
                    # This is an image marked with a keep tag
                    # don't even think about removing it
                    continue
            was_removed = check_remove_image(image, oldest_allowed)
            if was_removed:
                deleted_count += 1

    if not ENABLE_DELETE:
        print('{} images would have been pruned'.format(deleted_count))
    else:
        print('{} images were pruned'.format(deleted_count))
