import requests

bot_token = "7227476930:AAHz9Aldcx4G2cTiyyZsEfkpyUirNeSffqY"
chat_ids = ["904798847", "841257571"] 

res = requests.get(f"https://api.telegram.org/bot{bot_token}/getUpdates").json()
print(res)

# message = f"Приветик, Киса! Поиграем?"
# for id in chat_ids:
#     requests.get(f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={id}&text={message}").json()