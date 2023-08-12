import openai
import SETTINGS
import xlsxwriter
import time
import traceback
import asyncio
from urllib import request, parse

# Настройки программы
settings = SETTINGS.get_settings()
if settings.DEBUG:
    print(f"settings={settings}")

openai.api_key = settings.openai_api_key
openai.organization = settings.openai_organization


def query_gpt(prompt, model="gpt-3.5-turbo"):
    chat_completion = openai.ChatCompletion.create(model=model, messages=[{"role": "user", "content": prompt}])
    return chat_completion.choices[0].message.content.rstrip('\n')


async def query3(prompt, model="gpt-3.5-turbo"):
    chat_completion = await openai.ChatCompletion.acreate(model=model, messages=[{"role": "user", "content": prompt}])
    return chat_completion.choices[0].message.content.rstrip('\n')


def query2(prompt, model="gpt-3.5-turbo"):
    """
    Запрос к CG
    :param prompt: Текст запроса (можно много строк)
    :param model: Модель CG см. файл list_of_models.txt
    :return: Ответ на запрос.
    """
    # try:
    #     chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k-0613",
    #                                                    messages=[{"role": "user", "content": prompt}])
    # except:
    #     raise
    chat_completion = openai.ChatCompletion.create(model=model,
                                                   messages=[{"role": "user", "content": prompt}])
    return chat_completion.choices[0].message.content.rstrip('\n')


def telegram_notification(message):
    """
    Оповещения в Телеграм. Настройки берутся из SETTINGS.py.
    :param message: Сообщение отправляемое в Телеграм.
    """
    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)     Chrome/37.0.2049.0 Safari/537.36'
    # }
    params = {
        'chat_id': settings.ZM_TELEGRAM_CHAT,
        'disable_web_page_preview': '1',
        'parse_mode': 'HTML',
        'text': message
    }
    # print(f"params={params}")
    data = parse.urlencode(params).encode()
    # print(f"data={data}")
    url = f"https://api.telegram.org/bot{settings.ZM_TELEGRAM_BOT_TOKEN}/sendMessage"
    # print(f"url={url}")
    # req = request.Request(url, data=data, method='POST', headers=headers)
    req = request.Request(url, data=data, method='POST')
    # print(f"req={req}")
    resp = request.urlopen(req)
    # print(f"resp={resp}")


def mass_query_01():
    """
    Цикл по текстовому файлу с фильтрацией дублей. Для каждого дубля просто берётся готовое описание, сформированное CG. Т.е. для всех дублей получаются одни и те же описания.
    :return:
    """
    start = time.time()  # Текущее время
    prefix = "составь описание автозапчасти примерно на 1000 символов без наименования:\n"
    # Обработка списка товаров из текстового файла
    workbook = xlsxwriter.Workbook(settings.excel_file)
    try:
        worksheet = workbook.add_worksheet('Список')
        with open(settings.journal_text_file, "w") as output:
            with open(settings.text_file, "r", encoding="utf-8") as f:
                i = 0  # Индекс текущей строки
                u = 0  # Индекс уникальных строки
                first_line = f.readline().strip('\n')  # Первая строка
                previous_line = first_line
                result = query2(prefix + first_line)
                print(f"{str(i).zfill(4)} | {time.time() - start} сек. | {first_line}")
                worksheet.write(i, 0, first_line)
                worksheet.write(i, 1, result)
                output.write(f"{first_line}\t{result}\n")
                i += 1
                for line in f:
                    line = line.strip('\n')
                    if line == previous_line:
                        u += 1
                    else:
                        result = query2(prefix + line)
                        previous_line = line
                    worksheet.write(i, 0, line)
                    worksheet.write(i, 1, result)
                    output.write(f"{line}\t{result}\n")
                    i += 1
                    print(f"{str(i).zfill(4)} | {time.time() - start} сек. | {line}")
            workbook.close()
    except Exception as e:
        workbook.close()
        f.close()
        output.close()
        err_text = f"Error: {e}"
        # err_line = f"{str(i).zfill(4)} | {time.time() - start} сек. | {line}"
        err_stack = traceback.format_exc()
        print(err_text)
        # print(err_line)
        print(err_stack)
        # print(f"=111==========================================")
        telegram_notification(f"❌ {err_text}")
        # telegram_notification(err_line)
        # print(f"=222==========================================")
        # telegram_notification(f"<code>{err_stack}</code>")

    end = time.time() - start  # собственно время работы программы
    message_text = f"Время работы программы: {end} сек. | Всего строк  {i} | Всего уникальных строк {u}"
    print(message_text)
    telegram_notification(f"✅ {message_text}")


def mass_query_02():
    """
    Цикл по текстовому файлу БЕЗ фильтрацией дублей. Т.е. для каждой строки формируется своё описание.
    :return:
    """
    start = time.time()  # Текущее время
    prefix = "составь описание автозапчасти примерно на 1000 символов без наименования:\n"
    # Обработка списка товаров из текстового файла
    workbook = xlsxwriter.Workbook(settings.excel_file)
    try:
        worksheet = workbook.add_worksheet('Список')
        with open(settings.journal_text_file, "w") as output:
            with open(settings.text_file, "r", encoding="utf-8") as f:
                i = 0  # Индекс текущей строки
                for line in f:
                    line = line.strip('\n')
                    result = query2(prefix + line)
                    worksheet.write(i, 0, line)
                    worksheet.write(i, 1, result)
                    output.write(f"{line}\t{result}\n")
                    i += 1
                    print(f"{str(i).zfill(4)} | {time.time() - start} сек. | {line}")
            workbook.close()
    except Exception as e:
        workbook.close()
        f.close()
        output.close()
        err_text = f"Error: {e}"
        # err_line = f"{str(i).zfill(4)} | {time.time() - start} сек. | {line}"
        err_stack = traceback.format_exc()
        print(err_text)
        # print(err_line)
        print(err_stack)
        # print(f"=111==========================================")
        telegram_notification(f"❌ {err_text}")
        # telegram_notification(err_line)
        # print(f"=222==========================================")
        # telegram_notification(f"<code>{err_stack}</code>")

    end = time.time() - start  # собственно время работы программы
    message_text = f"Время работы программы: {end} сек. | Всего строк  {i}"
    print(message_text)
    telegram_notification(f"✅ {message_text}")


async def mass_query_03():
    """
    Цикл по текстовому файлу БЕЗ фильтрацией дублей. Т.е. для каждой строки формируется своё описание.
    Если возникает ошибка, то скрипт становится на паузу и затем повторяет обработку этой строки ещё раз.
    :return:
    """
    start = time.time()  # Текущее время
    prefix = "составь описание автозапчасти примерно на 1000 символов без наименования:\n"
    # Read data from text file settings.journal_text_file to list
    with open(settings.text_file, "r", encoding="utf-8") as f:
        list_data = [line.rstrip() for line in f]
    # print(list_data[0])

    # Обрабатываем все строки и заносим результат в память в виде списка sets - list[(), (), ...]
    i = 0  # Индекс текущей строки
    result_list = []
    error_count = 1
    while i < len(list_data):
        try:
            # result = query2(prefix + list_data[i])
            result = await query3(prefix + list_data[i])
            result_list.append((list_data[i], result))
            print(f"{str(i).zfill(4)} | {time.time() - start} сек. | {list_data[i]}")
            error_count = 1
        except Exception as e:
            print(f"Error: {e}\n{traceback.format_exc()}")
            if error_count > 3:
                telegram_notification(f"❌ Количество ошибок больше 3")
                break
            i -= 1
            error_count += 1
            print(f"\n\nПауза {60 * error_count} сек.\n\n")
            time.sleep(60 * error_count)  # Пауза в случае ошибки.
        i += 1

    # Запись результата в текстовый файл (на всякий случай)
    try:
        with open(settings.journal_text_file, "w") as output:
            for line in result_list:
                output.write(f"{line[0]}\t{line[1]}\n")
    except Exception as e:
        output.close()
        err_text = f"Error: {e}\n{traceback.format_exc()}"
        print(err_text)
        telegram_notification(f"❌ {err_text}")
        exit(1)

    # Запись результата в Excel
    workbook = xlsxwriter.Workbook(settings.excel_file)
    try:
        worksheet = workbook.add_worksheet('Список')
        for idx, line in enumerate(result_list):
            worksheet.write(idx, 0, line[0])
            worksheet.write(idx, 1, line[1])
        workbook.close()
    except Exception as e:
        workbook.close()
        err_text = f"Error: {e}\n{traceback.format_exc()}"
        print(err_text)
        telegram_notification(f"❌ {err_text}")
        exit(1)

    end = time.time() - start  # собственно время работы программы
    message_text = f"Время работы программы: {end} сек. | Всего строк  {i}"
    print(message_text)
    telegram_notification(f"✅ {message_text}")


def test_query():
    """
    Тестирование запроса.
    """
    print(query2("""Я продаю автозапчасти на сайте. Составь разное описание для каждой автозапчасти длиной от 1000 до 1500 символов: 
    Амортизатор задний (стойка) CX-5 (KE) 2012-2016
    Амортизатор задний (стойка) CX-5 (KE) 2012-2018
    Амортизатор задний (стойка) CX-5 (KE) 2012-2016
    Амортизатор задний (стойка) CX-5 (KE) 2012-2016""", model="gpt-3.5-turbo"))


if __name__ == '__main__':
    # test_query()
    # mass_query_01()
    # mass_query_02()
    # mass_query_03()
    # asyncio.run(mass_query_03())

    # Одиночный запрос
    question = ""
    answer = query_gpt(question, model="gpt-3.5-turbo")
    print(answer)
