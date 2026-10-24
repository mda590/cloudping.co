from chalice import Chalice, Cron
from chalicelib.calculate_avgs import calculate
from chalicelib.calculation_scheduler import schedule
from chalicelib.store_region_status import store
from chalicelib.alerting import check_and_alert

app = Chalice(app_name='scheduled_functions')

@app.schedule(Cron("10", "0,6,12,18", "*", "*", "?", "*"))
def calc_scheduler(event):
    schedule(calc_func_name="scheduled_functions-prod-calculate_avgs")

@app.lambda_function()
def calculate_avgs(event, context):
    return calculate(event)

@app.schedule(Cron("20", "0,6,12,18", "*", "*", "?", "*"))
def store_region_status(event):
    store()

@app.schedule(Cron("0", "12", "*", "*", "?", "*"))
def alerting_check(event):
    check_and_alert()
