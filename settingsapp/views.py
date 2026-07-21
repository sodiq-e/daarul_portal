from django.shortcuts import render, redirect
from django.contrib import messages
from .models import SchoolSettings, GalleryImage, HeroText, HeroButton
from .forms import SchoolSettingsForm, GalleryImageFormSet, GalleryImageForm, HeroTextFormSet, HeroButtonFormSet


def _ensure_demo_homepage_content(settings_obj):
    if not HeroText.objects.filter(school_settings=settings_obj).exists():
        HeroText.objects.create(
            school_settings=settings_obj,
            title='Excellence in Motion',
            subtitle='A premium learning experience for future leaders.',
            button_text='Explore School Life',
            button_url='https://example.com',
            order=1,
            active=True,
            animation_type='fade',
            display_seconds=4,
        )
        HeroText.objects.create(
            school_settings=settings_obj,
            title='Faith, Knowledge, and Growth',
            subtitle='Nurturing confident students in a values-led community.',
            button_text='Meet the Community',
            button_url='https://example.com',
            order=2,
            active=True,
            animation_type='fade',
            display_seconds=4,
        )

    if not HeroButton.objects.filter(school_settings=settings_obj).exists():
        HeroButton.objects.create(school_settings=settings_obj, label='Apply for Admission', url='/apply/', order=1, active=True, open_in_new_tab=False)
        HeroButton.objects.create(school_settings=settings_obj, label='Contact Us', url='/contact/', order=2, active=True, open_in_new_tab=False)
        HeroButton.objects.create(school_settings=settings_obj, label='View Gallery', url='/gallery/', order=3, active=True, open_in_new_tab=False)


def school_settings(request):
    settings_obj, created = SchoolSettings.objects.get_or_create(id=1)
    _ensure_demo_homepage_content(settings_obj)
    gallery_images = GalleryImage.objects.filter(school_settings=settings_obj).order_by('order')
    hero_texts_qs = settings_obj.hero_texts.all().order_by('order')
    hero_buttons_qs = settings_obj.hero_buttons.all().order_by('order')

    if request.method == 'POST':
        form = SchoolSettingsForm(request.POST, request.FILES, instance=settings_obj)
        # Handle gallery image formset
        gallery_formset = GalleryImageFormSet(request.POST, request.FILES, queryset=gallery_images, prefix='gallery')
        # Hero text and button formsets
        hero_text_formset = HeroTextFormSet(request.POST, queryset=hero_texts_qs, prefix='herotext')
        hero_button_formset = HeroButtonFormSet(request.POST, queryset=hero_buttons_qs, prefix='herobutton')

        if form.is_valid():
            form.save()

            # Process gallery formset
            if gallery_formset.is_valid():
                instances = gallery_formset.save(commit=False)
                for instance in instances:
                    if not instance.school_settings_id:
                        instance.school_settings = settings_obj
                    instance.save()
                for obj in gallery_formset.deleted_objects:
                    obj.delete()
            else:
                messages.error(request, gallery_formset.errors)

            # Process hero text formset
            if hero_text_formset.is_valid():
                ht_instances = hero_text_formset.save(commit=False)
                for instance in ht_instances:
                    if not instance.school_settings_id:
                        instance.school_settings = settings_obj
                    instance.save()
                for obj in hero_text_formset.deleted_objects:
                    obj.delete()
            else:
                messages.error(request, hero_text_formset.errors)

            # Process hero button formset
            if hero_button_formset.is_valid():
                hb_instances = hero_button_formset.save(commit=False)
                for instance in hb_instances:
                    if not instance.school_settings_id:
                        instance.school_settings = settings_obj
                    instance.save()
                for obj in hero_button_formset.deleted_objects:
                    obj.delete()
            else:
                messages.error(request, hero_button_formset.errors)

            messages.success(request, 'School settings and media updated successfully!')

            return redirect('school_settings')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = SchoolSettingsForm(instance=settings_obj)
        gallery_formset = GalleryImageFormSet(queryset=gallery_images, prefix='gallery')
        hero_text_formset = HeroTextFormSet(queryset=hero_texts_qs, prefix='herotext')
        hero_button_formset = HeroButtonFormSet(queryset=hero_buttons_qs, prefix='herobutton')

    context = {
        'form': form,
        'gallery_formset': gallery_formset,
        'gallery_images': gallery_images,
        'hero_text_formset': hero_text_formset,
        'hero_button_formset': hero_button_formset,
        'hero_texts': hero_texts_qs,
        'hero_buttons': hero_buttons_qs,
    }
    return render(request, 'school_settings.html', context)


def gallery(request):
    """Public gallery page showing full images and playable video."""
    settings_obj, created = SchoolSettings.objects.get_or_create(id=1)
    gallery_images = GalleryImage.objects.filter(school_settings=settings_obj).order_by('order')

    context = {
        'school_settings': settings_obj,
        'gallery_images': gallery_images,
    }
    return render(request, 'gallery.html', context)
