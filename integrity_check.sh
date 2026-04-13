#!/bin/bash
KEY='/home/testuser/.ssh/backup_key'
REMOTE='borguser@192.168.56.20'
LOG='/var/log/integrity.log'

echo "$(date): Starting integrity check" >> $LOG

# Получаем эталон с VM-BACKUP
# Атакующий не может подменить файл на VM-BACKUP
scp -i $KEY $REMOTE:/store/checksums_original.txt /tmp/checksums_ref.txt

# Генерируем текущие хеши всех файлов
find /home/testuser/important_data -type f | sort | \
    xargs sha256sum > /tmp/checksums_current.txt

# Сортируем оба файла для корректного сравнения
sort /tmp/checksums_ref.txt > /tmp/ref_sorted.txt
sort /tmp/checksums_current.txt > /tmp/cur_sorted.txt

# Сравниваем хеши
DIFF=$(diff /tmp/ref_sorted.txt /tmp/cur_sorted.txt)
if [ -z "$DIFF" ]; then
    echo "$(date): OK — все файлы целы" >> $LOG
else
    echo "$(date): ALERT — файлы изменены!" >> $LOG
    echo "$DIFF" >> $LOG
fi
