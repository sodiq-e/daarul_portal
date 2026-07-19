# 15. Settings Module

## Feature Overview
The settings module manages school-wide settings, gallery content, page themes, and global school information.

## Core Features

### School Settings Management
- Entry point: /settings/school-settings/
- View: school_settings
- Form: SchoolSettingsForm
- Template: templates/school_settings.html

Workflow:
1. Admin opens the school settings page
2. School settings values are loaded from SchoolSettings
3. Form is submitted with optional gallery images
4. The settings object and gallery images are updated
5. A success message is displayed

### Gallery Page
- Entry point: /gallery/
- View: gallery
- Template: templates/gallery.html

Purpose:
- display gallery images and video content configured in SchoolSettings and GalleryImage

## Models
- SchoolSettings
- GalleryImage
- PageTheme

## Dependencies
- Used by pages and communication context processors
- Supplies branding and static content to templates
