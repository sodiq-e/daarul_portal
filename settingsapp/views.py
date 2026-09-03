from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import SchoolSettings, GalleryImage, HeroText, HeroButton, Tenant
from .forms import SchoolSettingsForm, TenantForm, TenantMembershipForm, GalleryImageFormSet, GalleryImageForm, HeroTextFormSet, HeroButtonFormSet


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


def _get_request_settings_obj(request):
    tenant = getattr(request, 'tenant', None)

    if tenant is not None:
        settings_obj = getattr(tenant, 'portal_settings', None)
        if settings_obj is None:
            settings_obj = SchoolSettings.objects.create(tenant=tenant)
        return settings_obj

    settings_obj = SchoolSettings.objects.filter(tenant__isnull=True).first() or SchoolSettings.objects.order_by('id').first() or SchoolSettings.objects.create()
    return settings_obj


def tenant_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login')

    tenants = Tenant.objects.all().order_by('name')
    return render(request, 'tenant_dashboard.html', {'tenants': tenants})


@transaction.atomic
def tenant_form(request, tenant_id=None):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login')

    tenant = get_object_or_404(Tenant, pk=tenant_id) if tenant_id else None
    form = TenantForm(request.POST or None, instance=tenant)
    if request.method == 'POST' and form.is_valid():
        tenant = form.save()
        SchoolSettings.objects.get_or_create(tenant=tenant)
        messages.success(request, f'{tenant.name} tenant configuration saved.')
        return redirect('tenant_portal_settings', tenant_id=tenant.id)

    return render(request, 'tenant_form.html', {'form': form, 'tenant': tenant})


@transaction.atomic
def tenant_memberships(request, tenant_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login')

    tenant = get_object_or_404(Tenant, pk=tenant_id)
    if request.method == 'POST':
        form = TenantMembershipForm(request.POST, tenant=tenant)
        if form.is_valid():
            membership, _ = tenant.memberships.update_or_create(
                user=form.cleaned_data['user'],
                role=form.cleaned_data['role'],
                defaults={'is_active': form.cleaned_data['is_active']},
            )
            messages.success(request, f'{membership.user.username} assigned as {membership.get_role_display()}.')
            return redirect('tenant_memberships', tenant_id=tenant.id)
    else:
        form = TenantMembershipForm(tenant=tenant)

    memberships = tenant.memberships.select_related('user').order_by('user__username', 'role')
    return render(request, 'tenant_memberships.html', {
        'tenant': tenant,
        'form': form,
        'memberships': memberships,
    })


def platform_home(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login')

    tenants = Tenant.objects.all().order_by('name')
    return render(request, 'platform_home.html', {'tenants': tenants})


def tenant_portal_settings(request, tenant_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login')

    tenant = get_object_or_404(Tenant, pk=tenant_id)
    settings_obj = getattr(tenant, 'portal_settings', None) or SchoolSettings.objects.create(tenant=tenant)

    _ensure_demo_homepage_content(settings_obj)
    gallery_images = GalleryImage.objects.filter(school_settings=settings_obj).order_by('order')
    hero_texts_qs = settings_obj.hero_texts.all().order_by('order')
    hero_buttons_qs = settings_obj.hero_buttons.all().order_by('order')

    if request.method == 'POST':
        form = SchoolSettingsForm(request.POST, request.FILES, instance=settings_obj)
        gallery_formset = GalleryImageFormSet(request.POST, request.FILES, queryset=gallery_images, prefix='gallery')
        hero_text_formset = HeroTextFormSet(request.POST, queryset=hero_texts_qs, prefix='herotext')
        hero_button_formset = HeroButtonFormSet(request.POST, queryset=hero_buttons_qs, prefix='herobutton')

        form_valid = form.is_valid()
        gallery_valid = gallery_formset.is_valid()
        hero_text_valid = hero_text_formset.is_valid()
        hero_button_valid = hero_button_formset.is_valid()

        if form_valid and gallery_valid and hero_text_valid and hero_button_valid:
            form.save()
            instances = gallery_formset.save(commit=False)
            for instance in instances:
                if not instance.school_settings_id:
                    instance.school_settings = settings_obj
                instance.save()
            for obj in gallery_formset.deleted_objects:
                obj.delete()

            ht_instances = hero_text_formset.save(commit=False)
            for instance in ht_instances:
                if not instance.school_settings_id:
                    instance.school_settings = settings_obj
                instance.save()
            for obj in hero_text_formset.deleted_objects:
                obj.delete()

            hb_instances = hero_button_formset.save(commit=False)
            for instance in hb_instances:
                if not instance.school_settings_id:
                    instance.school_settings = settings_obj
                instance.save()
            for obj in hero_button_formset.deleted_objects:
                obj.delete()

            messages.success(request, f'Portal settings for {tenant.name} updated successfully!')
            return redirect('tenant_portal_settings', tenant_id=tenant.id)

        if not form_valid:
            messages.error(request, 'Please correct the errors in the form.')
        if not gallery_valid:
            messages.error(request, 'Please correct the errors in the gallery section.')
        if not hero_text_valid:
            messages.error(request, 'Please correct the errors in the hero animated text section.')
        if not hero_button_valid:
            messages.error(request, 'Please correct the errors in the hero CTA buttons section.')
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
        'tenant': tenant,
        'is_main_admin': True,
    }
    return render(request, 'school_settings.html', context)


def school_settings(request):
    tenant = getattr(request, 'tenant', None)

    if request.user.is_authenticated and not request.user.is_superuser and tenant is not None:
        raise Http404

    settings_obj = _get_request_settings_obj(request)

    if request.user.is_authenticated and request.user.is_superuser and tenant is None:
        tenant = Tenant.objects.order_by('id').first()
        if tenant is not None:
            settings_obj = getattr(tenant, 'portal_settings', None) or SchoolSettings.objects.create(tenant=tenant)

    _ensure_demo_homepage_content(settings_obj)
    gallery_images = GalleryImage.objects.filter(school_settings=settings_obj).order_by('order')
    hero_texts_qs = settings_obj.hero_texts.all().order_by('order')
    hero_buttons_qs = settings_obj.hero_buttons.all().order_by('order')

    if request.method == 'POST':
        form = SchoolSettingsForm(request.POST, request.FILES, instance=settings_obj)
        gallery_formset = GalleryImageFormSet(request.POST, request.FILES, queryset=gallery_images, prefix='gallery')
        hero_text_formset = HeroTextFormSet(request.POST, queryset=hero_texts_qs, prefix='herotext')
        hero_button_formset = HeroButtonFormSet(request.POST, queryset=hero_buttons_qs, prefix='herobutton')

        form_valid = form.is_valid()
        gallery_valid = gallery_formset.is_valid()
        hero_text_valid = hero_text_formset.is_valid()
        hero_button_valid = hero_button_formset.is_valid()

        if form_valid and gallery_valid and hero_text_valid and hero_button_valid:
            form.save()

            instances = gallery_formset.save(commit=False)
            for instance in instances:
                if not instance.school_settings_id:
                    instance.school_settings = settings_obj
                instance.save()
            for obj in gallery_formset.deleted_objects:
                obj.delete()

            ht_instances = hero_text_formset.save(commit=False)
            for instance in ht_instances:
                if not instance.school_settings_id:
                    instance.school_settings = settings_obj
                instance.save()
            for obj in hero_text_formset.deleted_objects:
                obj.delete()

            hb_instances = hero_button_formset.save(commit=False)
            for instance in hb_instances:
                if not instance.school_settings_id:
                    instance.school_settings = settings_obj
                instance.save()
            for obj in hero_button_formset.deleted_objects:
                obj.delete()

            messages.success(request, 'School settings and media updated successfully!')
            return redirect('school_settings')

        if not form_valid:
            messages.error(request, 'Please correct the errors in the form.')
        if not gallery_valid:
            messages.error(request, 'Please correct the errors in the gallery section.')
        if not hero_text_valid:
            messages.error(request, 'Please correct the errors in the hero animated text section.')
        if not hero_button_valid:
            messages.error(request, 'Please correct the errors in the hero CTA buttons section.')
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
        'tenant': tenant,
        'is_main_admin': request.user.is_authenticated and request.user.is_superuser,
    }
    return render(request, 'school_settings.html', context)


def gallery(request):
    """Public gallery page showing full images and playable video."""
    settings_obj = _get_request_settings_obj(request)
    gallery_images = GalleryImage.objects.filter(school_settings=settings_obj).order_by('order')

    context = {
        'school_settings': settings_obj,
        'gallery_images': gallery_images,
    }
    return render(request, 'gallery.html', context)
