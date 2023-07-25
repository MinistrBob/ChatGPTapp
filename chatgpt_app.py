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

# openai.api_key = "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"
openai.api_key = settings.openai_api_key
openai.organization = settings.openai_organization


def query(prompt):
    print("func query")
    # задаем модель и промпт
    model_engine = "gpt-3.5-turbo"

    # задаем макс кол-во слов
    max_tokens = 128

    # генерируем ответ
    completion = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1024,
        temperature=0.5,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    # выводим ответ
    print(completion.choices[0].text)
    print(f"\n====================\n")
    print(completion)
    print(f"\n====================\n")
    print(completion.choices)


def query2(prompt):
    # print("func query2")
    # create a chat completion
    # print(prompt)
    prompt = "составь описание автозапчасти примерно на 1000 символов без наименования:" + "\n" + prompt
    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k-0613",
                                                   messages=[{"role": "user", "content": prompt}])

    # print the chat completion
    # print(chat_completion.choices[0].message.content)

    # # выводим ответ
    # print(f"\n====================\n")
    # print(chat_completion)
    # print(f"\n====================\n")
    # print(chat_completion.choices)
    return chat_completion.choices[0].message.content.rstrip('\n')


def telegram_notification(message):
    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)     Chrome/37.0.2049.0 Safari/537.36'
    # }
    params = {
        'chat_id': settings.ZM_TELEGRAM_CHAT,
        'disable_web_page_preview': '1',
        'parse_mode': 'HTML',
        'text': message
    }
    print(f"params={params}")
    data = parse.urlencode(params).encode()
    print(f"data={data}")
    url = f"https://api.telegram.org/bot{settings.ZM_TELEGRAM_BOT_TOKEN}/sendMessage"
    print(f"url={url}")
    # req = request.Request(url, data=data, method='POST', headers=headers)
    req = request.Request(url, data=data, method='POST')
    print(f"req={req}")
    resp = request.urlopen(req)
    print(f"resp={resp}")


if __name__ == '__main__':
    telegram_notification("тест")
    exit(0)
    start = time.time()  ## точка отсчета времени
    # list models
    # models = openai.Model.list()
    # print(models)
    # exit(0)
    # print(f"\n====================\n")
    # try:
    #     query("what an awakening is")
    # except Exception as e:
    #     print(e)
    # print(f"\n====================\n")
    try:
        # Обработка списка товаров из текстового файла
        workbook = xlsxwriter.Workbook(settings.excel_file)
        worksheet = workbook.add_worksheet('Список')
        with open(settings.text_file, "r", encoding="utf-8") as f:
            i = 1  # Индекс текущей строки
            u = 1  # Индекс уникальных строки
            first_line = f.readline().strip('\n')  # Первая строка
            previous_line = first_line
            # print(first_line)
            result = query2(first_line)
            # result = f"result-{i}"
            # print(f"{first_line}\t{result}")
            # print(f"{first_line}")
            print(f"{time.time() - start}сек. | {first_line}")
            worksheet.write(i, 0, first_line)
            worksheet.write(i, 1, result)
            i += 1
            for line in f:
                line = line.strip('\n')
                # print(line)
                if line == previous_line:
                    # print(f"{line}\t{result}")
                    u += 1
                else:
                    # result = f"result-{i}"
                    result = query2(line)
                    # print(f"{line}\t{result}")
                    # print(f"{line}")
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
#     exit(0)
#     try:
#         query2("""составь описание автозапчасти примерно на 1000 символов без наименования:
# Щетки стеклоочистителя переднего M6 (GH) 2007-2012 (комплект)	3397118907
# Щетки стеклоочистителя переднего M6 (GH) 2007-2012 (комплект)	GSFB673309K""")
#     except Exception as e:
#         print(e)
