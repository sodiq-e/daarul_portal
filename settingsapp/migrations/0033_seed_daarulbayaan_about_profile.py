from django.db import migrations


DEFAULT_PROFILE_CONTENT = {
    'intro': (
        '<p>Daarul Bayaan Islamic School is an educational institution committed to nurturing '
        'children through a balanced blend of Islamic and Western education. We believe that '
        'education should do more than impart knowledge; it should shape character, strengthen '
        'faith, develop sound reasoning, and prepare children to become responsible members of '
        'society.</p>'
        '<p>Guided by our motto, &ldquo;Knowledge for the Fear of Allah,&rdquo; we seek to provide '
        'an educational foundation in which academic learning goes hand in hand with Islamic '
        'values, good manners, discipline, and a sense of responsibility.</p>'
        '<p>Our educational approach brings together foundational literacy and numeracy, Islamic '
        'studies, Qur&rsquo;an, Arabic, Hadith, STEM, robotics, and mental mathematics. Through '
        'these areas of learning, we aim to nurture children who can think critically, explore '
        'ideas, develop practical skills, and appreciate the relationship between knowledge, '
        'faith, and everyday life.</p>'
        '<p>At Daarul Bayaan, we see every stage of a child&rsquo;s education as an opportunity '
        'to build a strong foundation for lifelong learning, moral development, and purposeful '
        'living.</p>'
    ),
    'history': (
        '<p>Daarul Bayaan Islamic School was established with a commitment to providing children '
        'with an education that recognises the importance of both intellectual development and '
        'Islamic upbringing.</p>'
        '<p>The school grew from the conviction that children deserve an educational foundation '
        'that equips them with the knowledge and skills needed to navigate the modern world while '
        'remaining grounded in their faith, values, and sense of responsibility.</p>'
        '<p>With a focus on nursery and primary education, Daarul Bayaan seeks to nurture young '
        'learners during their formative years, helping them develop curiosity, confidence, good '
        'character, and a love for learning.</p>'
        '<p>As the school grows, its guiding purpose remains clear: to make meaningful education '
        'one that develops the mind, nurtures the character, and encourages the pursuit of '
        'knowledge with an awareness of one&rsquo;s responsibility to Allah and humanity.</p>'
    ),
    'motto': 'Knowledge for the Fear of Allah',
    'vision': (
        '<p>To nurture a generation of knowledgeable, morally upright, confident, and innovative '
        'individuals who are grounded in Islamic values, equipped with relevant knowledge and '
        'skills, and prepared to contribute positively to society.</p>'
    ),
    'mission': (
        '<p>To provide quality education that integrates Islamic teachings with contemporary '
        'academic learning; nurture faith, good character, discipline, and sound moral judgment; '
        'develop literacy, numeracy, creativity, critical thinking, and practical problem-solving '
        'skills; and create an educational environment that encourages curiosity, responsibility, '
        'and a lifelong love of learning.</p>'
        '<p>Through purposeful teaching and age-appropriate learning experiences, we aim to lay a '
        'strong foundation for every child&rsquo;s intellectual, moral, spiritual, and social '
        'development.</p>'
    ),
    'leadership_message': (
        '<p>At Daarul Bayaan Islamic School, we recognise that the education of a child is a shared '
        'responsibility between the school and the family. We therefore value the trust parents '
        'place in us and recognise the importance of working together to support each child&rsquo;s '
        'development.</p>'
        '<p>Our commitment goes beyond academic instruction. We aspire to nurture children who '
        'appreciate knowledge, demonstrate good character, respect others, and understand the '
        'importance of living by sound moral and Islamic principles.</p>'
        '<p>We also recognise the importance of preparing children for a changing world. By '
        'combining foundational academic learning with Islamic education, creativity, technology, '
        'and practical problem-solving, we seek to provide an educational experience that supports '
        'the development of the whole child.</p>'
        '<p>As our school continues to grow, we remain committed to purposeful learning, continuous '
        'improvement, and the values that define our identity.</p>'
        '<p>We look forward to building a meaningful partnership with our parents and community as '
        'we work together towards a brighter future for our children.</p>'
    ),
    'educational_approach': (
        '<p>At Daarul Bayaan Islamic School, we believe that meaningful education should develop '
        'the whole child. Our educational approach seeks to combine strong academic foundations '
        'with Islamic learning, practical skills, creativity, and character development.</p>'
        '<h3>Islamic Education and Moral Development</h3>'
        '<p>Islamic learning is an important part of our educational identity. Through areas such '
        'as Qur&rsquo;an, Arabic, Hadith, and Islamic studies, we seek to help pupils develop '
        'religious understanding and appreciate the importance of faith, good manners, honesty, '
        'discipline, and responsibility.</p>'
        '<h3>Strong Academic Foundations</h3>'
        '<p>We recognise the importance of literacy, numeracy, communication, and sound reasoning '
        'in a child&rsquo;s educational journey. Our approach aims to help pupils build the '
        'foundational knowledge and skills they need for continued learning and future academic '
        'development.</p>'
        '<h3>STEM, Robotics, and Innovation</h3>'
        '<p>We believe children should have opportunities to explore how things work, ask '
        'questions, experiment with ideas, and solve practical problems. STEM and robotics '
        'introduce pupils to logical thinking, creativity, technology, and the relationship '
        'between scientific ideas and the world around them.</p>'
        '<h3>Mental Mathematics and Problem-Solving</h3>'
        '<p>We encourage the development of numerical confidence, concentration, reasoning, and '
        'problem-solving through mental mathematics and other appropriate learning activities.</p>'
        '<h3>Learning with Character and Purpose</h3>'
        '<p>We believe academic progress is most meaningful when accompanied by good character. '
        'We therefore seek to encourage responsibility, perseverance, cooperation, respect, and '
        'the ability to apply knowledge thoughtfully in everyday life.</p>'
        '<p>Through this balanced approach, Daarul Bayaan aims to establish a strong foundation '
        'for children to grow in knowledge, character, confidence, and purpose.</p>'
    ),
}


DEFAULT_SECTIONS = [
    (
        'value',
        'Faith and God-consciousness',
        'We encourage children to recognise Allah&rsquo;s place in their lives and to approach '
        'the pursuit of knowledge with sincerity, humility, and a sense of responsibility.',
    ),
    (
        'value',
        'Good Character and Integrity',
        'We promote honesty, kindness, respect, discipline, and good manners, helping pupils '
        'understand that character is an essential part of true education.',
    ),
    (
        'value',
        'Excellence in Learning',
        'We encourage pupils to develop their abilities, pursue understanding, take their '
        'learning seriously, and strive to improve through effort and perseverance.',
    ),
    (
        'value',
        'Curiosity and Innovation',
        'We nurture children&rsquo;s natural curiosity and encourage them to ask questions, '
        'explore ideas, solve problems, and discover new possibilities through creative and '
        'practical learning.',
    ),
    (
        'value',
        'Responsibility and Discipline',
        'We encourage pupils to take responsibility for their actions, respect others, care for '
        'their environment, and develop habits that support personal growth.',
    ),
    (
        'value',
        'Compassion and Respect',
        'We promote consideration for others, fairness, cooperation, and respect for the dignity '
        'of every person.',
    ),
    (
        'value',
        'Knowledge with Purpose',
        'We believe knowledge should be acquired and applied responsibly, guided by sound values '
        'and used to benefit individuals, families, and society.',
    ),
    (
        'custom',
        'Early Childhood Education',
        'We recognise the importance of the early years in a child&rsquo;s development. Our '
        'nursery and cr&egrave;che learning pathways aim to establish foundations for '
        'communication, early literacy, numeracy, social development, curiosity, and readiness '
        'for further learning.',
    ),
    (
        'custom',
        'Primary Education',
        'Our primary education programme focuses on strengthening foundational knowledge and '
        'skills while encouraging independent thinking, responsibility, confidence, and '
        'readiness for the next stage of education.',
    ),
    (
        'custom',
        'Qur&rsquo;an and Islamic Studies',
        'We incorporate Islamic learning into our educational identity, with an emphasis on '
        'Qur&rsquo;an, Arabic, Hadith, and the development of Islamic understanding and good '
        'character.',
    ),
    (
        'custom',
        'STEM and Robotics',
        'We introduce pupils to scientific thinking, technology, creativity, and practical '
        'problem-solving through age-appropriate STEM and robotics learning experiences.',
    ),
    (
        'custom',
        'Mental Mathematics',
        'We encourage pupils to strengthen numerical fluency, concentration, logical reasoning, '
        'and confidence in working with numbers.',
    ),
]


def seed_daarulbayaan_about_profile(apps, schema_editor):
    Tenant = apps.get_model('settingsapp', 'Tenant')
    SchoolSettings = apps.get_model('settingsapp', 'SchoolSettings')
    SchoolAboutProfile = apps.get_model('settingsapp', 'SchoolAboutProfile')
    SchoolAboutSection = apps.get_model('settingsapp', 'SchoolAboutSection')

    tenant = Tenant.objects.filter(slug='daarulbayaan').first()
    if tenant is None:
        return

    school_settings = SchoolSettings.objects.filter(tenant_id=tenant.pk).first()
    if school_settings is None:
        return

    profile, created = SchoolAboutProfile.objects.get_or_create(
        school_settings_id=school_settings.pk,
        defaults=DEFAULT_PROFILE_CONTENT,
    )
    if not created:
        fields_to_update = []
        for field_name, default_value in DEFAULT_PROFILE_CONTENT.items():
            if not (getattr(profile, field_name) or '').strip():
                setattr(profile, field_name, default_value)
                fields_to_update.append(field_name)
        if fields_to_update:
            profile.save(update_fields=fields_to_update)

    if SchoolAboutSection.objects.filter(school_about_id=profile.pk).exists():
        return

    SchoolAboutSection.objects.bulk_create([
        SchoolAboutSection(
            school_about_id=profile.pk,
            section_type=section_type,
            title=title,
            content=f'<p>{content}</p>',
            order=order,
            is_active=True,
        )
        for order, (section_type, title, content) in enumerate(DEFAULT_SECTIONS, start=1)
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('settingsapp', '0032_schoolaboutprofile_schoolaboutsection'),
    ]

    operations = [
        migrations.RunPython(seed_daarulbayaan_about_profile, migrations.RunPython.noop),
    ]
