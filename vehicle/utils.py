from .models import *
from calender.models import *
from calender.views import connect_sql
import math

def convert_number(string):
    response = string

    if isinstance(response, float):
        response = str(round(response))

    if ',00' in response:
        response = response.replace(',00', '')
    if '.' in response:
        response = response.replace('.', '')
    return float(response)

def cal_fee_on_km(km_total, vehicle_id, create_date=None):

    vehicle = Vehicle.objects.get(id=vehicle_id)

    fuel_type = vehicle.fuel_type
    fuel_rate = vehicle.fuel_rate

    # Fuel liter total depends on kilometer total
    liter_total = 0.0
    if fuel_rate and km_total:
        liter_total = km_total / (100 / fuel_rate.name)

    # Amount total depends on fuel price
    amount_total = 0.0
    if liter_total and fuel_type:
        amount_total = liter_total * fuel_type.price

        return amount_total
    return 0.0

def cal_liter_on_km(km_total, vehicle_id, create_date=None):

    vehicle = Vehicle.objects.get(id=vehicle_id)

    fuel_type = vehicle.fuel_type
    fuel_rate = vehicle.fuel_rate

    # Fuel liter total depends on kilometer total
    liter_total = 0.0
    if fuel_rate and km_total:
        liter_total = km_total / (100 / fuel_rate.name)
        return liter_total
    return 0.0

def get_user_management_depart(user_id):
    # ID=105 is 'BQLDA'
    sql = """SELECT au.id FROM auth_user au INNER JOIN 
        calender_profile cp ON au.id = cp.user_id INNER JOIN 
        calender_department cd ON cp.department_id = cd.id WHERE au.id = %s AND cp.department_id = 105""" % (user_id)
    data = connect_sql(sql)

    if len(data) > 0:
        return True
    return False


class Calculation(object):
    @staticmethod
    def crane_liter(crane_hour_total, vehicle_id, rate_type, create_date=None):
        vehicle = Vehicle.objects.get(id=vehicle_id)
        if rate_type == "crane":
            fuel_rate = vehicle.crane_fuel_rate
        else:
            fuel_rate = vehicle.generator_firing_fuel_rate

        # Fuel liter total depends on crane hour total
        liter_total = 0.0
        if fuel_rate and crane_hour_total:
            liter_total = crane_hour_total * fuel_rate.name
            return liter_total
        return 0.0

    @staticmethod
    def convert_comma(number):
        if not number:
            return 0
        frac, whole = math.modf(number)
        if frac > 0.0:
            return f"{number: ,.2f}"
        return f"{number: ,.0f}"

    @staticmethod
    def convert_dot(number):
        if not number:
            return 0
        frac, whole = math.modf(number)
        if frac > 0.0:
            return f"{number: ,.2f}"
        return f"{number: ,.0f}".replace(',', '.')


def find_fuel_price(fueltype, start_time):
    sql = f"""
        SELECT price FROM vehicle_fueltype WHERE name = N'{fueltype}' 
        AND start_time <= '{start_time}' AND end_time >= '{start_time}'
        ORDER BY create_date DESC
        """
    data = connect_sql(sql)
    if len(data) > 0:
        return data[0]['price']
    return 0