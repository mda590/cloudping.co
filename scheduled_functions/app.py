from chalice import Chalice, Cron
from chalicelib.calculate_avgs import calculate
from chalicelib.calculation_scheduler import schedule

app = Chalice(app_name='scheduled_functions')

@app.schedule(Cron("10", "0,6,12,18", "*", "*", "?", "*"))
def calc_scheduler(event):
    schedule(calc_func_name="scheduled_functions-prod-calculate_avgs")


@app.lambda_function()
def calculate_avgs(event, context):
    calculate(event)
