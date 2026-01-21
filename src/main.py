# -*- coding: utf-8 -*-

import mysql.connector
from .app.reports.statistical_report import StatisticalReport
from .app.reports.detailed_report import DetailedReport

def connect_to_db():
    return mysql.connector.connect(
        host="pma.goncharuk.info",
        user="phpmyadmin",
        password="0907",
        database="phpmyadmin"
    )

if __name__ == "__main__":
    conn = connect_to_db()
    stat_report = StatisticalReport(conn)
    detail_report = DetailedReport(conn)
    
    stat_report.run('statistic_report.pdf')
    detail_report.run('detail_report.pdf')
    
    print("otchet")