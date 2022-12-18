import requests as requests
from terminaltables import AsciiTable
from environs import Env


env = Env()
env.read_env()
sj_token = env('SJ_TOKEN')

PROGRAMMING_LANGUAGES = ('Javascript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C', 'Go', 'Shell', 'Objective-C',
                         'Scala', 'Swift', 'TypeScript')
HH_MOSCOW_ID = 1
SJ_MOSCOW_ID = 4
SJ_PROGRAMMING_CATALOG_ID = 48


def predict_salary(salary_from, salary_to):
    if not salary_from and not salary_to:
        return None
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    if salary_from:
        return salary_from * 1.2
    if salary_to:
        return salary_to * 0.8


def predict_rub_salary_hh(vacancy):
    salary = vacancy['salary']
    if not salary:
        return None
    if salary['currency'] != 'RUR':
        return None
    return predict_salary(salary['from'], salary['to'])


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
            'area': HH_MOSCOW_ID,
            'page': 0
        }
        while params['page'] < pages_number:
            hh_response = requests.get("https://api.hh.ru/vacancies/", params=params)
            hh_response.raise_for_status()
            page_vacancies = hh_response.json()
            vacancies.extend(page_vacancies['items'])
            pages_number = page_vacancies['pages']
            params['page'] += 1

        vacancies_processed = 0
        salaries_sum = 0
        for vacancy in vacancies:
            salary = predict_rub_salary_hh(vacancy)
            if salary:
                salaries_sum += salary
                vacancies_processed += 1
        if not vacancies_processed:
            average_salary = 0
        else:
            average_salary = int(salaries_sum / vacancies_processed)
        report[language] = {
            "vacancies_found": page_vacancies['found'],
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }
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
            'town': SJ_MOSCOW_ID,
            'catalogues': SJ_PROGRAMMING_CATALOG_ID,
            'page': 0
        }
        more = True
        while more:
            sj_response = requests.get("https://api.superjob.ru/2.0/vacancies/", params=params, headers=headers)
            sj_response.raise_for_status()
            page_vacancies = sj_response.json()
            more = page_vacancies['more']
            vacancies.extend(page_vacancies['objects'])
            params['page'] += 1
        vacancies_processed = 0
        salaries_sum = 0
        for vacancy in vacancies:
            salary = predict_rub_salary_sj(vacancy)
            if salary:
                salaries_sum += salary
                vacancies_processed += 1
        if not vacancies_processed:
            average_salary = 0
        else:
            average_salary = int(salaries_sum / vacancies_processed)
        report[language] = {
            "vacancies_found": page_vacancies['total'],
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }
    return report


def get_salary_table(report: dict, table_title):
    salary_table = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for prog_lang in report:
        salary_table.append([prog_lang, *(report[prog_lang].values())])
    salary_table = AsciiTable(salary_table, table_title)
    return salary_table.table


def main():
    sj_report = get_sj_report()
    hh_report = get_hh_report()
    print(get_salary_table(sj_report, 'SuperJob Moscow'))
    print(get_salary_table(hh_report, 'HeadHunter Moscow'))


if __name__ == '__main__':
    main()
