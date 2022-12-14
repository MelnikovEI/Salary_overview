import requests as requests
from terminaltables import AsciiTable
from environs import Env


env = Env()
env.read_env()
sj_token = env('SJ_TOKEN')

PROGRAMMING_LANGUAGES = ('Javascript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C', 'Go', 'Shell', 'Objective-C',
                         'Scala', 'Swift', 'TypeScript')


def predict_salary(salary_from, salary_to):
    if salary_from:
        if salary_to:
            return (salary_from + salary_to) / 2
        else:
            return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    else:
        return None


def predict_rub_salary_hh(vacancy):
    salary_info = vacancy['salary']
    if not salary_info:
        return None
    if salary_info['currency'] != 'RUR':
        return None
    return predict_salary(salary_info['from'], salary_info['to'])


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] != 'rub':
        return None
    return predict_salary(vacancy['payment_from'], vacancy['payment_to'])


def get_hh_report():
    report = {}
    for language in PROGRAMMING_LANGUAGES:
        pages_number = 1
        vacancies = []
        params = {
            'text': language,
            'area': 1,
            'page': 0
        }
        while params['page'] < pages_number:
            hh_response = requests.get("https://api.hh.ru/vacancies/", params=params)
            hh_response.raise_for_status()
            page_vacancies = hh_response.json()
            vacancies.extend(page_vacancies['items'])
            pages_number = page_vacancies['pages']
            print('headhunter', language, ': processed page ', params['page'] + 1, ' from ', pages_number)
            params['page'] += 1

        vacancies_processed = 0
        salaries_sum = 0
        for vacancy in vacancies:
            salary = predict_rub_salary_hh(vacancy)
            if salary:
                salaries_sum += salary
                vacancies_processed += 1
        if vacancies_processed == 0:
            average_salary = 0
        else:
            average_salary = int(salaries_sum / vacancies_processed)
        report.update({
            language:
                {
                    "vacancies_found": page_vacancies['found'],
                    "vacancies_processed": vacancies_processed,
                    "average_salary": average_salary
                }
        })
    return report


def get_sj_report():
    headers = {
        'X-Api-App-Id': sj_token,
    }
    report = {}
    for language in PROGRAMMING_LANGUAGES:
        vacancies = []
        params = {
            'keyword': language,
            'town': 4,
            'catalogues': 48,
            'page': 0
        }
        more = True
        while more:
            sj_response = requests.get("https://api.superjob.ru/2.0/vacancies/", params=params, headers=headers)
            sj_response.raise_for_status()
            page_vacancies = sj_response.json()
            more = page_vacancies['more']
            vacancies.extend(page_vacancies['objects'])
            print('superjob', language, ': processed page ', params['page'] + 1)
            params['page'] += 1
        vacancies_processed = 0
        salaries_sum = 0
        for item in vacancies:
            salary = predict_rub_salary_sj(item)
            if salary:
                salaries_sum += salary
                vacancies_processed += 1
        if vacancies_processed == 0:
            average_salary = 0
        else:
            average_salary = int(salaries_sum / vacancies_processed)
        report.update({
            language:
                {
                    "vacancies_found": page_vacancies['total'],
                    "vacancies_processed": vacancies_processed,
                    "average_salary": average_salary
                }
        })
    return report


def print_report(report: dict, table_title):
    table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for prog_lang in report:
        table_data.append([prog_lang, *(report[prog_lang].values())])
    salary_table = AsciiTable(table_data, table_title)
    print(salary_table.table)


sj_report = get_sj_report()
hh_report = get_hh_report()
print_report(sj_report, 'SuperJob Moscow')
print_report(hh_report, 'HeadHunter Moscow')
