#!/bin/bash
KEY='/home/testuser/.ssh/backup_key'
REMOTE='borguser@192.168.56.20'
LOG='/var/log/integrity.log'
WATCH_DIR='/home/testuser/important_data'

echo "$(date): Integrity monitor started" >> $LOG

# inotifywait ждёт событий изменения файлов
# -r рекурсивно, -e close_write,moved_to,create,delete — события записи
inotifywait -r -m -e close_write,moved_to,create,delete \
    --format '%w%f %e' "$WATCH_DIR" 2>/dev/null | \
while read filepath event; do
    echo "$(date): File changed: $filepath ($event)" >> $LOG

    # Получаем эталон с VM-BACKUP
    # Используем borg serve канал — scp не работает через command= ключ
    # Поэтому эталон получаем через отдельный административный ключ
    scp -i /root/.ssh/admin_key \
        $REMOTE:/store/checksums_original.txt \
        /tmp/checksums_ref.txt 2>/dev/null

    if [ $? -ne 0 ]; then
        # Если VM-BACKUP недоступен — используем локальный эталон
        # Он создан от root и недоступен testuser
        cp /root/checksums_original.txt /tmp/checksums_ref.txt
    fi

    # Проверяем изменённый файл
    CURRENT_HASH=$(sha256sum "$filepath" 2>/dev/null | awk '{print $1}')
    EXPECTED_HASH=$(grep "$filepath" /tmp/checksums_ref.txt | awk '{print $1}')

    if [ "$CURRENT_HASH" != "$EXPECTED_HASH" ]; then
        echo "$(date): ALERT — integrity violation: $filepath" >> $LOG
        echo "$(date): Expected: $EXPECTED_HASH" >> $LOG
        echo "$(date): Got:      $CURRENT_HASH" >> $LOG
    fi
done
