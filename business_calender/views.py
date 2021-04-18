from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from calender import views as V

def public(request):
    return HttpResponse("Welcome to public page")

@login_required
def private(request):
    return HttpResponse("Welcome to private page")

def get_start_and_end_date_from_calendar_week(year, calendar_week):       
	monday = datetime.strptime(f'{year}-{calendar_week-1}-1', "%Y-%W-%w").date()
	return monday, monday + timedelta(days=6.9)

def shows(request, week):
    date_list = []
    current_week = datetime.now().isocalendar()
    # If current week of year equal passing week number
    if current_week[1] == week:
        # print("equalllllllllllllllllllllllllllllllllllllllllll")
        today = datetime.now().strftime('%Y-%m-%d')     # Convert datetime into string
        today = datetime.strptime(today, '%Y-%m-%d').date()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=7)
        ymd_today = today.strftime('%Y-%m-%d')
        ymd_end = end.strftime('%Y-%m-%d')
        range_date = end - today
    else:
        # print("elseeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
        current_year = current_week[0]                  # (year, week_num, day_of_week)
        ls_date = get_start_and_end_date_from_calendar_week(current_year, week)
        today = ls_date[0]
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=7)
        ymd_today = today.strftime('%Y-%m-%d')
        ymd_end = end.strftime('%Y-%m-%d')
        range_date = end - today
    start_date = start.strftime('%d/%m/%Y')
    end_date = (start + timedelta(days=6)).strftime('%d/%m/%Y')
    # print('today: ', today)
    # print('start: ', start)
    # print('end: ', end)
    # print('range_date: ', range_date.days)
    for i in range(range_date.days):
        item = {}
        dmy = today + timedelta(days=i)
        d = dmy.strftime('%d-%m-%Y')
        ymd = dmy.strftime('%Y-%m-%d')
        item['date'] = d
        item['day'] = V.week(dmy.strftime('%A'))
        sql = """select CONVERT(VARCHAR(10), start_time, 105) as date, week, count(CONVERT(VARCHAR(10), start_time, 105)) as count 
            from calender_calender cc inner join calender_department cd on cc.chair_unit_id= cd.id where slide_show = 1 and 
            CONVERT(VARCHAR(10), start_time, 21) = '{}'
            and status in ('DONE')
            group by week, CONVERT(VARCHAR(10), start_time, 105)""".format(ymd)
        # print('sql {}: {}'.format(i, sql))
        count = V.connect_sql(sql)

        item['count'] = count[0]['count'] if len(count)>0 else 0
        date_list.append(item)
    # print('date_list: ', date_list)

    sql_calender = """select CONVERT(VARCHAR(10), start_time, 105) as date, CONVERT(VARCHAR(5), start_time, 108) as starttime, CONVERT(VARCHAR(5), end_time, 108) as endtime, cc.*, cd.name, coalesce(cm.name, '') as meeting_name, ROW_NUMBER() OVER (
        PARTITION BY CONVERT(VARCHAR(10), start_time, 105)
        ORDER BY CONVERT(VARCHAR(5), start_time, 108)
        ) row_num from calender_calender cc
        inner join calender_department cd on cc.chair_unit_id= cd.id 
        left join calender_meeting cm on cc.location_id = cm.id
        where status in ('DONE') and slide_show = 1 and start_time between '{}' and '{}' order by start_time asc""".format(ymd_today, ymd_end)
    data = V.connect_sql(sql_calender)
    # print('sql_calender: ', sql_calender)
    # print('data: ', len(data))
    if data:
        for i in data:
            sql_joins = """select cjc.calender_id, cd.name from calender_department cd inner join calender_joincomponent cjc on cd.id = cjc.department_id where cjc.calender_id = {}""".format(i['id'])
            rs_joins = V.connect_sql(sql_joins)
            item_join = [ j['name'] for j in rs_joins if j['calender_id']]
            i['join_component'] = item_join

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'date_list': date_list,
        'calender': data
    }

    return render(request, "calender/shows.html", context)