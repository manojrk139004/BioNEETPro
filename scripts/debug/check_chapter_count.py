from syllabus import syllabus_validator
count = 0
for class_key, class_data in syllabus_validator.syllabus.items():
    for unit_key, unit_data in class_data.items():
        for chap_id, chap_data in unit_data['chapters'].items():
            count += 1
            print(f'{chap_id}: {chap_data["chapter_name"]}')
print(f'Total chapters: {count}')