import openai
import SETTINGS
import xlsxwriter
import time
import traceback
from urllib import request, parse

# Настройки программы
settings = SETTINGS.get_settings()
if settings.DEBUG:
    print(f"settings={settings}")

openai.api_key = settings.openai_api_key
openai.organization = settings.openai_organization


def query2(prompt):
    prompt = "составь описание автозапчасти примерно на 1000 символов без наименования:" + "\n" + prompt
    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k-0613",
                                                   messages=[{"role": "user", "content": prompt}])
    return chat_completion.choices[0].message.content.rstrip('\n')


def telegram_notification(message):
    params = {
        'chat_id': settings.ZM_TELEGRAM_CHAT,
        'disable_web_page_preview': '1',
        'parse_mode': 'HTML',
        'text': message
    }
    data = parse.urlencode(params).encode()
    url = f"https://api.telegram.org/bot{settings.ZM_TELEGRAM_BOT_TOKEN}/sendMessage"
    req = request.Request(url, data=data, method='POST')
    resp = request.urlopen(req)


if __name__ == '__main__':
    start = time.time()  # Текущее время
    # Обработка списка товаров из текстового файла
    workbook = xlsxwriter.Workbook(settings.excel_file)
    try:
        worksheet = workbook.add_worksheet('Список')
        with open(settings.text_file, "r", encoding="utf-8") as f:
            i = 1  # Индекс текущей строки
            u = 1  # Индекс уникальных строки
            first_line = f.readline().strip('\n')  # Первая строка
            previous_line = first_line
            result = query2(first_line)
            print(f"{time.time() - start}сек. | {first_line}")
            worksheet.write(i, 0, first_line)
            worksheet.write(i, 1, result)
            i += 1
            for line in f:
                line = line.strip('\n')
                if line == previous_line:
                    u += 1
                else:
                    result = query2(line)
                    previous_line = line
                worksheet.write(i, 0, line)
                worksheet.write(i, 1, result)
                i += 1
                print(f"{i.zfill(4)} | {time.time() - start} сек. | {line}")
        workbook.close()
    except Exception as e:
        err_text = f"Error: {e}"
        err_line = f"{i.zfill(4)} | {time.time() - start} сек. | {line}"
        err_stack = traceback.format_exc()
        print(err_text)
        print(err_line)
        print(err_stack)
        telegram_notification(err_text)
        telegram_notification(err_line)
        telegram_notification(err_stack)
    finally:
        workbook.close()
    end = time.time() - start  # собственно время работы программы
    message_text = f"Время работы программы: {end} сек. | Всего строк  {i} | Всего уникальных строк {u}"
    print(message_text)
    telegram_notification(message_text)
