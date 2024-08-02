from datetime import datetime, timedelta

active_phrases = ("В наличии", "Под заказ", "Активно")
inactive_phrases = ("Нет в наличии", "Снято с публикации", "Истёк срок публикации", "В архиве", "Отклонено", "Заблокировано")

def change_dateend(isAvailable, avitoStatus, yesterday):
    try:
        if isAvailable in active_phrases or avitoStatus in active_phrases:
            dateend = float("nan")
            
        if isAvailable in inactive_phrases or avitoStatus in inactive_phrases:
            dateend = yesterday
    except:
        dateend = float("nan")
    return dateend