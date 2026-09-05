from syllabus import syllabus_validator
for class_key, class_data in syllabus_validator.syllabus.items():
    for unit_key, unit_data in class_data.items():
        for chap_id, chap_data in unit_data['chapters'].items():
            print(f'{chap_id}: {chap_data["chapter_name"]}')