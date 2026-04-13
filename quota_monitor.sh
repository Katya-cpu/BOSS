#!/bin/bash
LOG='/var/log/quota_alert.log'
LIMIT=80  # порог срабатывания в процентах

USED=$(repquota /store | grep borguser | awk '{print $3}')
HARD=$(repquota /store | grep borguser | awk '{print $5}')

if [ "$HARD" -gt 0 ]; then
    PERCENT=$((USED * 100 / HARD))
    if [ "$PERCENT" -ge "$LIMIT" ]; then
        echo "$(date): ALERT! borguser quota ${PERCENT}% used" >> $LOG
        echo "$(date): Blocking SSH access for borguser!" >> $LOG
        # Убиваем все активные SSH сессии borguser
        pkill -u borguser
        # Блокируем новые SSH подключения по ключу
        chmod 000 /home/borguser/.ssh/authorized_keys
        echo "$(date): borguser SSH BLOCKED — all sessions killed" >> $LOG
    else
        echo "$(date): OK — quota ${PERCENT}% used" >> $LOG
    fi
fi
