from django.shortcuts import render, redirect
from django.contrib import messages
from .models import SchoolSettings, GalleryImage
from .forms import SchoolSettingsForm, GalleryImageFormSet, GalleryImageForm

def school_settings(request):
    settings_obj, created = SchoolSettings.objects.get_or_create(id=1)
    gallery_images = GalleryImage.objects.filter(school_settings=settings_obj).order_by('order')

    if request.method == 'POST':
        form = SchoolSettingsForm(request.POST, request.FILES, instance=settings_obj)
        # Handle gallery image formset
        gallery_formset = GalleryImageFormSet(request.POST, request.FILES, queryset=gallery_images, prefix='gallery')

        if form.is_valid():
            form.save()

            # Process gallery formset
            if gallery_formset.is_valid():
                # Save the formset (handles deletions and updates)
                instances = gallery_formset.save(commit=False)

                # Set the school_settings for new instances
                for instance in instances:
                    if not instance.school_settings_id:  # New instance
                        instance.school_settings = settings_obj
                    instance.save()

                # Delete removed images
                for obj in gallery_formset.deleted_objects:
                    obj.delete()

                messages.success(request, 'School settings and gallery updated successfully!')
            else:
                messages.error(request, gallery_formset.errors)

            return redirect('school_settings')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = SchoolSettingsForm(instance=settings_obj)
        gallery_formset = GalleryImageFormSet(queryset=gallery_images, prefix='gallery')

    context = {
        'form': form,
        'gallery_formset': gallery_formset,
        'gallery_images': gallery_images,
    }
    return render(request, 'school_settings.html', context)
