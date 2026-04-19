#!/usr/bin/env python
"""Fix missing user profiles"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daarul_portal.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile

# Create profiles for users without them
users_without_profiles = User.objects.filter(profile__isnull=True)
count = 0

for user in users_without_profiles:
    Profile.objects.create(user=user)
    print(f"✓ Created profile for user: {user.username}")
    count += 1

if count > 0:
    print(f"\n✓ Successfully created {count} profile(s)")
else:
    print("✓ All users already have profiles")
