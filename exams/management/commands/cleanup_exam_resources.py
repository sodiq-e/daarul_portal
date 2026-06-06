from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
import os
import time
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Cleanup old exam resource uploads older than EXAM_UPLOAD_CLEANUP_DAYS'

    def handle(self, *args, **options):
        days = getattr(settings, 'EXAM_UPLOAD_CLEANUP_DAYS', 90)
        cutoff = datetime.now() - timedelta(days=days)
        prefix = 'exam_resources'
        self.stdout.write(f'Cleaning up files under {prefix}/ older than {days} days (cutoff {cutoff})')

        # default_storage may be remote; attempt to use listdir if available
        try:
            for root, dirs, files in default_storage.listdir(prefix):
                for fname in files:
                    rel = os.path.join(prefix, fname)
                    try:
                        # only works for file system storage where path() exists
                        path = default_storage.path(rel)
                        mtime = datetime.fromtimestamp(os.path.getmtime(path))
                        if mtime < cutoff:
                            default_storage.delete(rel)
                            self.stdout.write(f'Deleted {rel}')
                    except NotImplementedError:
                        self.stdout.write(f'Skipping {rel}: storage.path not implemented')
                    except Exception as e:
                        self.stdout.write(f'Error checking {rel}: {e}')
        except Exception as e:
            self.stdout.write(f'Error listing storage: {e}')
