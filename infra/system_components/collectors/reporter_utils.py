from infra.allure_report_handler.reporter import Reporter


def attach_log_to_allure_report(collector, log_path):
    log_content = collector.os_station.get_file_content(file_path=log_path)
    Reporter.attach_str_as_file(file_name=log_path, file_content=log_content)
