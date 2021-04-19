from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from datetime import datetime, timedelta
from django.db import connection
from django.conf import settings
import os, mimetypes
from django.utils.encoding import smart_str
from .models import Calender as CalenderModel, Department, ExpectedCalender, MultipleFile, Working_Division
import xlsxwriter
from django.contrib.auth import authenticate, login
import json, re
from django.core.files.storage import FileSystemStorage
from . import ldap_test
from dotenv import load_dotenv
from os.path import join, dirname
from pathlib import Path  # python3 only
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import JSONParser
from .serializers import ExpectedSerialize
import requests
# import bugsnag
from .forms import CalenderChangeForm, CalenderForm, FileFormSet, CalenderFormSet, DisableForm, FileForm
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.forms import inlineformset_factory
from django.contrib.auth.models import Permission, ContentType
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Create your views here.
def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def connect_sql(query, *params):
    with connection.cursor() as cursor:
        if len(params)>0:
            cursor.execute(query, params)
            rows = dictfetchall(cursor)
        else:
            cursor.execute(query)
            rows = dictfetchall(cursor)
    return rows

def getWeek(request):
    if request.method == "POST":
        # print("postttttttttttttttttttttttt getWeek")
        date = request.POST['date']
        data = start_end_of_week(date)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        group = getGroupUserId(user_id)
        #print(group)
        group_list = [i['group_id'] for i in group]
        #print(group_list)
        week = convertNumberWeek(date)
        status = check_Calender(date, department_id)
        # print(status)
        calender = getCalender(department_id, date)
        date_list = dateOfWeek(department_id, date)
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'week': week,
            'department_name': department[0]['department_name'],
            'group': group,
            'group_list': group_list,
            'status': status,
            'date_list': date_list,
            'calender': calender
        }
        return render(request, "calender/reload.html", context)

def getWeek_draf(request):
    if request.method == "POST": #os request.GET()
        # print("postttttttttttttttttttttttt getWeek_draf")
        date = request.POST['date']
        start = request.POST['start']
        chair_unit_id = request.POST['value']
        data = start_end_of_week(start)
        week = convertNumberWeek(start)
        status = check_Calender(date, chair_unit_id)
        # print('get status with chair_unit_id: ' + status)
        if chair_unit_id == "0":
            title_status = "LỊCH CÔNG TY"
        else:
            title_status = "LỊCH PHÒNG"
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        calender = getCalender_draf(start, chair_unit_id)
        date_list = dateOfWeek_draf(start, chair_unit_id)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        context = {
            'date_draf': date,
            'start_draf': data['start'],
            'end_draf': data['end'],
            'title_status': title_status,
            'status_draf': status,
            'week_draf': week,
            'list_chair_unit': list_chair_unit,
            'department_id': chair_unit_id,
            'date_list_draf': date_list,
            'calender_draf': calender,
            'group_list': group_list,
            'duid': department_id
        }
        return render(request, "calender/reload_draf.html", context)

def get_status(status_id):
    if status_id == 0:
        return "Bình thường"
    elif status_id == 1:
        return "Huỷ/Hoãn"
    elif status_id == 2:
        return "Thay đổi"
    elif status_id == 3:
        return "Bổ sung"
    elif status_id == 4:
        return "Đột xuất"
    elif status_id == 5:
        return "Đổi địa điểm"
    else:
        return "Đổi thời gian"

def export_xlsx(request):
    if request.method == "GET":
        date = request.GET['date']
        depart_id = request.GET['depart_id'] or "0"
        state = request.GET['status']
        # print("date: ", date)
        # print("depart_id: ", depart_id)
        # print("state: ", state)
        arr_date = datetime.now().strftime('%d-%m-%Y').split("-")
        # print(date)
        data = get_date(date, depart_id, state)
    # print('data: ', data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = "attachment; filename=week.xlsx"
    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook(response, {'in_memory': True})
 
    worksheet = workbook.add_worksheet()

    # Add a number format for cells with worksheet.
    format1 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True, 'text_wrap': 1})
    format2 = workbook.add_format({'font_size': 12, 'align': 'center', 'text_wrap': 1, 'border': 1})
    format_date = workbook.add_format({'font_size': 12, 'align': 'right', 'text_wrap': 1})
    format_date.set_italic()
    format_justify = workbook.add_format({'font_size': 12, 'text_wrap': 1, 'border': 1})
    format_title = workbook.add_format({'font_size': 12, 'align': 'center', 'text_wrap': 1, 'bold': True, 'border': 1})
    format1.set_align('center')
    format1.set_align('vcenter')
    format2.set_align('center')
    format2.set_align('vcenter')
    format_justify.set_align('justify')
    format_justify.set_align('vcenter')
    format_title.set_align('center')
    format_title.set_align('vcenter')
    format1.set_font('Times New Roman')
    format2.set_font('Times New Roman')
    format_justify.set_font('Times New Roman')
    format_title.set_font('Times New Roman')
    format_date.set_font('Times New Roman')
    format_title.set_bg_color('#F0FFFF')
    worksheet.insert_image('A2', 'calender/static/calender/images/logo.png', {'x_scale': 1, 'y_scale': 1})
    worksheet.print_area('A1:H20')
    worksheet.fit_to_pages(1, 0)
    worksheet.set_landscape()
    worksheet.set_paper(9)
    worksheet.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)

    worksheet.set_column(6, 0, 15)
    worksheet.set_column(6, 1, 15)
    worksheet.set_column(6, 2, 20)
    worksheet.set_column(6, 3, 35)
    worksheet.set_column(6, 4, 25)
    worksheet.set_column(6, 5, 20)
    worksheet.set_column(6, 6, 30)
    worksheet.set_column(6, 7, 15)
    worksheet.set_row(6, 30)

    worksheet.merge_range('A2:H2', 'TỔNG CÔNG TY ĐIỆN LỰC MIỀN TRUNG', format1)
    worksheet.merge_range('A3:H3', 'CÔNG TY ĐIỆN LỰC QUẢNG NAM', format1)
    worksheet.merge_range('A5:H5', 'LỊCH CÔNG TÁC TUẦN '+str(data['week'])+' - TỪ NGÀY '+data['start']+' ĐẾN NGÀY '+data['end'], format1)
    worksheet.merge_range('A6:H6', 'Ngày in: '+arr_date[0]+' tháng '+arr_date[1]+' năm '+arr_date[2], format_date)

    worksheet.write('A7', 'Thứ/Ngày', format_title)
    worksheet.write('B7', 'Thời gian', format_title)
    worksheet.write('C7', 'Địa điểm', format_title)
    worksheet.write('D7', 'Nội dung', format_title)
    worksheet.write('E7', 'Chuẩn bị', format_title)
    worksheet.write('F7', 'Chủ trì', format_title)
    worksheet.write('G7', 'Thành phần', format_title)
    worksheet.write('H7', 'Trạng thái', format_title)

    begin_row = 7
    arr_seq = []
    arr_seq.append(begin_row)
    # Iterate over the data and write it out row by row (Thứ/ Ngày)
    for index, item in enumerate(data['date_list']):
        if item['count'] == 0 or item['count'] == 1:
            worksheet.write(begin_row, 0, item['day']+"\n ("+item['date'][0:5]+")",format2)
            begin_row += 1
        else:
            worksheet.merge_range(begin_row, 0, begin_row + item['count'] - 1, 0, item['day']+"\n ("+item['date'][0:5]+")",format2)
            begin_row = begin_row + item['count']
        # print("begin_rowwwwwwwwwwwwwwwwwwwwww: ", begin_row)
        if len(arr_seq) < 7:
            arr_seq.append(begin_row)

        # Iterate over the data and write it out row by row (Lịch)
        row_count = arr_seq[index]
        for item_info in data['calender']:
            if item['date'] == item_info['date']:
                join_component = ", ".join(item_info['join_component'])
                if item_info['other_component']:
                    if join_component:
                        join_component += ", "+item_info['other_component']
                    else:
                        join_component = item_info['other_component']
                prepare_unit = ", ".join(item_info['prepare_unit'])
                if item_info['other_prepare']:
                    if prepare_unit:
                        prepare_unit += ", "+item_info['other_prepare']
                    else:
                        prepare_unit = item_info['other_prepare']

                status = get_status(item_info['cancel_status'])
                worksheet.write(row_count, 1, item_info['starttime']+' - '+item_info['endtime'], format2)
                worksheet.write(row_count, 2, item_info['meeting_name'] if item_info['meeting_name'] else item_info['address'], format_justify)
                worksheet.write(row_count, 3, item_info['content'], format_justify)
                worksheet.write(row_count, 4, prepare_unit, format2)
                worksheet.write(row_count, 5, item_info['name'], format2)
                worksheet.write(row_count, 6, join_component, format_justify)
                worksheet.write(row_count, 7, status, format2)
                row_count = row_count + 1
            
            # print("arr_seq[index]: ", arr_seq[index])
        
        if item['count'] == 0:
            worksheet.write(row_count, 1, '', format2)
            worksheet.write(row_count, 2, '', format_justify)
            worksheet.write(row_count, 3, '', format_justify)
            worksheet.write(row_count, 4, '', format2)
            worksheet.write(row_count, 5, '', format2)
            worksheet.write(row_count, 6, '', format_justify)
            worksheet.write(row_count, 7, '', format2)
    # print("arr: ", arr_seq)
    # print("len arr: ", len(arr_seq))
    
    worksheet.merge_range(begin_row + 1, 0, begin_row + 1, 2, 'Dự kiến lịch công tác tuần sau:', format1)
    begin_row_ex = begin_row + 2
    # print("data['expected_list']: ", data['expected_list'])
    for ex in data['expected_list']:
        worksheet.merge_range(begin_row_ex, 0, begin_row_ex, 7, ex['content'], format_justify)
        begin_row_ex += 1

    begin_row_footer = begin_row_ex + 1
    
    worksheet.merge_range(begin_row_footer, 5, begin_row_footer, 6, 'TL.GIÁM ĐỐC', format1)
    worksheet.merge_range(begin_row_footer + 1, 5, begin_row_footer + 1, 6, 'CHÁNH VĂN PHÒNG', format1)

    workbook.close()
    return response

def approval_calender(request):
    # print("approval_calender")
    if request.method == "POST":
        date = request.POST['date']
        #print(date)
        data = start_end_of_week(date)
        week = convertNumberWeek(date)
        status = getCalenderStatus_vt(week)
        #print(status)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        # calender = getCalender_vt(date)
        # date_list = dateOfWeek_vt(date)
        calender = get_calender_type(date, department_id, "approval")
        date_list = dateOfWeek_type(date, department_id, "approval")
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'week': week,
            'list_chair_unit': list_chair_unit,
            'date_list': date_list,
            'calender': calender
        }
        return render(request, "calender/approval.html", context)

def execute_sql(query, *params):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
    return True

def browse(request):
    # print("browseeeeeeeeeeeeeeeeeeeeeeeeeeeê")
    if request.method == 'POST':
        data_string = request.POST.get('json_data')
        data_dict = json.loads(data_string)
        date = data_dict['info']['date']
        start = data_dict['info']['start']
        listIdCalender = data_dict['info']['listIdCalender']
        listIdCalender_notCheck = data_dict['info']['listIdCalender_notCheck']
        data = start_end_of_week(start)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        week = convertNumberWeek(start)
        for item in listIdCalender:
            sql = "UPDATE calender_calender SET check_calender=1, status='ACCEPT', write_date = %s WHERE id = %s"
            execute_sql(sql, datetime.now(), item)
            
        for item in listIdCalender_notCheck:
            sql = "UPDATE calender_calender SET check_calender=0, status='NEW', write_date = %s WHERE id = %s"
            execute_sql(sql, datetime.now(), item)
            
        status = check_Calender(date, department_id)
        # print(status)
        
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        calender = getCalender(department_id, start)
        date_list = dateOfWeek(department_id, start)
        
        context = {
            'date': date,
            'week': week,
            'start': data['start'],
            'end': data['end'],
            'department_name': department[0]['department_name'],
            'group': group,
            'group_list': group_list,
            'status': status,
            'date_list': date_list,
            'calender': calender
        }
        return render(request, "calender/reload.html", context)

#kiểm tra lịch tuần: có dữ liệu chưa, lịch mới, đã duyệt, đã ban hành
def check_Calender(date, department_id):
    week = convertNumberWeek(date)
    year = date.split('-')[-1]          # Get last element of list
    check_calender = 'DONE'
    if department_id == "0":
        sql = "select status from calender_calender where week = %s and YEAR(start_time) = %s"
        data = connect_sql(sql, week, year)
    else:
        sql = "select status from calender_calender where week = %s and YEAR(start_time) = %s and create_depart_id_id = %s"
        data = connect_sql(sql, week, year, department_id)
    if len(data) == 0:
        return 'NONE'
    else:
        for item in data:
            if item['status'] == 'NEW':
                return 'NEW'
        if department_id == "0":
            sql = "select status from calender_calender where status <> 'NEW' and week = %s and YEAR(start_time) = %s"
            data = connect_sql(sql, week, year)
        else:
            sql = "select status from calender_calender where status <> 'NEW' and week = %s and YEAR(start_time) = %s and create_depart_id_id = %s"
            data = connect_sql(sql, week, year, department_id)
        for item in data:
            if item['status'] == 'ACCEPT':
                return 'ACCEPT'
    return check_calender

def cancel(request):
    # print("canceleeeeeeeeeeeeeeeeeeeeeeeê")
    if request.method == 'POST':
        data_string = request.POST.get('json_data')
        data_dict = json.loads(data_string)
        date = data_dict['info']['date']
        start = data_dict['info']['start']
        listIdCalender = data_dict['info']['listIdCalender']
        data = start_end_of_week(start)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        week = convertNumberWeek(start)
        for item in listIdCalender:
            sql = "UPDATE calender_calender SET check_calender=0, status='NEW', write_date = %s WHERE id = %s"
            execute_sql(sql, datetime.now(), item)
        
        status = check_Calender(date, department_id)
        # print(status)
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        calender = getCalender(department_id, start)
        date_list = dateOfWeek(department_id, start)
        
        context = {
            'date': date,
            'week': week,
            'start': data['start'],
            'end': data['end'],
            'department_name': department[0]['department_name'],
            'group': group,
            'group_list': group_list,
            'status': status,
            'date_list': date_list,
            'calender': calender
        }
        return render(request, "calender/reload.html", context)

def download(request):
    # print("downloadeeeeeeeeeeeeeeeeeeeeeeeeeeeê")
    file_name = request.GET['download']
    # print(file_name)
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    if os.path.exists(file_path):
        filename = open(file_path, "r")
        mime_type, _ = mimetypes.guess_type(file_path)
        response = HttpResponse(filename, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response
    raise Http404

def fileUploaderView(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        idcalender = request.POST.get('idcalender')
        for myfile in request.FILES.getlist('arrFile[]'):
            # print(myfile)
            fs = FileSystemStorage()
            filename = fs.save(myfile.name, myfile)
            fs.url(filename)
            # sql = "UPDATE calender_calender SET attach_file=%s WHERE id=%s";
            if MultipleFile.objects.filter(files=filename).exists() == False:
                sql = "INSERT INTO calender_multiplefile(files, create_date, calendar_id) VALUES (%s, %s, %s)"
                execute_sql(sql, filename, datetime.now(), idcalender)
        data = start_end_of_week(date)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        group = getGroupUserId(user_id)
        group_list =  [i['group_id'] for i in group]
        week = convertNumberWeek(date)
        status = check_Calender(date, department_id)
        # print('statussssssssss: ', status)
        calender = getCalender(department_id, date)
        date_list = dateOfWeek(department_id, date)
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'week': week,
            'department_name': department[0]['department_name'],
            'group': group,
            'group_list': group_list,
            'status': status,
            'date_list': date_list,
            'calender': calender
        }
        return render(request, "calender/reload.html", context)

def uploadfileDepartmentDraft(request):
    # print("uploadfileeeeeeeeee")
    if request.method == 'POST':
        date = request.POST.get('date')
        idcalender = request.POST.get('idcalender')
        # print(date)
        # print(idcalender)
        # print(request.FILES.getlist('arrFile[]'))
        for myfile in request.FILES.getlist('arrFile[]'):
            # print(myfile)
            fs = FileSystemStorage()
            filename = fs.save(myfile.name, myfile)
            fs.url(filename)
            # sql = "UPDATE calender_calender SET attach_file=%s WHERE id=%s";
            if MultipleFile.objects.filter(files=filename).exists() == False:
                sql = "INSERT INTO calender_multiplefile(files, create_date, calendar_id) VALUES (%s, %s, %s)"
                execute_sql(sql, filename, datetime.now(), idcalender)
        state = request.POST.get('status')
        user_id = request.user.pk
        department = getDepartment(user_id)
        chair_unit_id = department[0]['department_id']
        
        data = start_end_of_week(date)
        group = getGroupUserId(user_id)
        # print('grouppppppppppppp re-render: ', group)
        group_list = [i['group_id'] for i in group]
        week = convertNumberWeek(date)
        status = check_calender_letter(date, chair_unit_id)
        # print("check_calender_letter state DEP: ", status)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        # calender = getCalender_draf(date, chair_unit_id)
        # date_list = dateOfWeek_draf(date, chair_unit_id)
        calender = get_calender_type(date, chair_unit_id, state)
        date_list = dateOfWeek_type(date, chair_unit_id, state)
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'status': status,
            'week': week,
            'group': group,
            'department_id': chair_unit_id,
            'date_list': date_list,
            'calender': calender,
            'group_list': group_list,
            'list_chair_unit': list_chair_unit
        }
        return render(request, "calender/department_draft.html", context)

def uploadfileRelease(request):
    # print("uploadfileeeeeeeeee")
    if request.method == 'POST':
        date = request.POST.get('date')
        idcalender = request.POST.get('idcalender')
        depart_id = request.POST.get('depart_id')
        # print(request.FILES.getlist('arrFile[]'))
        for myfile in request.FILES.getlist('arrFile[]'):
            fs = FileSystemStorage()
            filename = fs.save(myfile.name, myfile)
            fs.url(filename)
            # print('filename: ', filename)
            # sql = "UPDATE calender_calender SET attach_file=%s WHERE id=%s";
            if MultipleFile.objects.filter(files=filename).exists() == False:
                sql = "INSERT INTO calender_multiplefile(files, create_date, calendar_id) VALUES (%s, %s, %s)"
                execute_sql(sql, filename, datetime.now(), idcalender)
        state = request.POST.get('status')
        user_id = request.user.pk
        department = getDepartment(user_id)
        chair_unit_id = department[0]['department_id']
        
        data = start_end_of_week(date)
        group = getGroupUserId(user_id)
        # print('grouppppppppppppp re-render: ', group)
        group_list = [i['group_id'] for i in group]
        week = convertNumberWeek(date)
        list_users = getlistusers(chair_unit_id)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        calender = get_calender_type(date, depart_id, state)
        date_list = dateOfWeek_type(date, depart_id, state)
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'week': week,
            'department_id': chair_unit_id,
            'list_chair_unit': list_chair_unit, 
            'group_list': group_list,
            'list_users': list_users,
            'date_list': date_list,
            'calender': calender
        }
        return render(request, "calender/data.html", context)

def deletefileRelease(request):
    # print("uploadfileeeeeeeeee")
    if request.method == 'POST':
        date = request.POST.get('date')
        file_id = request.POST.get('file_id')
        depart_id = request.POST.get('depart_id')

        # print('date: ', date)
        # print('file_id: ', file_id)
        # print('depart_id: ', depart_id)

        sql_file = "select files from calender_multiplefile where id = %s"
        file_item = connect_sql(sql_file, file_id)

        sql = "delete calender_multiplefile where id = %s"
        execute_sql(sql, file_id)

        # print('file_item: ', len(file_item))
        if len(file_item) > 0:
            for f in file_item:
                try:
                    path = settings.MEDIA_ROOT + "\\" + f['files']
                    # print('path: ', path)
                    exist = os.path.exists(path)
                    if exist:
                        os.remove(path)
                except ValueError as e:
                    # print('ValueError: ', e)
                    continue

        user_id = request.user.pk
        department = getDepartment(user_id)
        chair_unit_id = department[0]['department_id']
        
        data = start_end_of_week(date)
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        week = convertNumberWeek(date)
        list_users = getlistusers(chair_unit_id)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        calender = get_calender_type(date, depart_id, 'approval')
        date_list = dateOfWeek_type(date, depart_id, 'approval')
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'week': week,
            'department_id': chair_unit_id,
            'list_chair_unit': list_chair_unit, 
            'group_list': group_list,
            'list_users': list_users,
            'date_list': date_list,
            'calender': calender
        }
        return render(request, "calender/data.html", context)
   

def upload(f):
    file = open(f.name, 'wb+')
    for chunk in f.chunks():
        file.write(chunk)  

def filter_chair(request):
    # print("filter_chairrrrrrrrrrrrrr")
    if request.method == "POST":
        date = request.POST['start']
        #date = '25-05-2020'
        chair_unit_id = request.POST['value']
        status = request.POST['status']
        #print(date)
        # print(chair_unit_id)
        data = start_end_of_week(date)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        parent_id = department[0]['parent_id']
        # print('department_id: ', department_id)
        week = convertNumberWeek(date)
        # print('status: ', status)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        getDepart = getDepartmentUserId(user_id)
        list_users = getlistusers(getDepart[0]['department_id'])
        calender = get_calender_type(date, chair_unit_id, status)
        date_list = dateOfWeek_type(date, chair_unit_id, status)
        # print(calender[0]['prepare_unit_ids'])
        #print(date_list)
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'week': week,
            'chair_unit_id': chair_unit_id,
            'list_chair_unit': list_chair_unit, 
            'group_list': group_list,
            'list_users': list_users,
            'date_list': date_list,
            'calender': calender,
            'department_id': department_id,
            'parent_id': parent_id
        }
        return render(request, "calender/data.html", context)

def getlistusers(department_id):
    sql = "select * from auth_user where id in (select user_id from calender_profile where department_id = %s)"
    data = connect_sql(sql, department_id)
    return data

class Calender(View):
    def get(self, request):
        # print("postttttttttttttttttttttttt")
        # date = request.POST['date']
        now = datetime.strptime(datetime.now().strftime('%d-%m-%Y'), '%d-%m-%Y').date()
        date_next_week = now + timedelta(days=7)
        start_date = date_next_week - timedelta(days=date_next_week.weekday())
        date = start_date.strftime('%d-%m-%Y')
        # print('date: ', date)
        data = start_end_of_week(date)
        # print(data)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        # print("group_listttttttttttt: ", group_list)
        week = convertNumberWeek(date)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        if 3 in group_list:
            # department_id = '0'
            # Check approval of the department draft
            status = check_calender_letter(date, department_id)
            # Check approval of the letter draft
            status_evn = check_calender_letter(date, department_id)
            # print("statusssss: ", status)
            # print("statusssss env: ", status_evn)
            calender = get_calender_type(date, department_id, "draft")
            date_list = dateOfWeek_type(date, department_id, "draft")
            # calender = getCalender(department_id, date)
            # date_list = dateOfWeek(department_id, date)

            calender_evn = get_calender_type(date, department_id, "draft-company")
            date_list_evn = dateOfWeek_type(date, department_id, "draft-company")
            context = {
                'date': date,
                'start': data['start'],
                'end': data['end'],
                'week': week,
                'department_name': department[0]['department_name'],
                'group': group,
                'group_list': group_list,
                'status': status,
                'date_list': date_list,
                'calender': calender,
                'date_evn': date,
                'start_evn': data['start'],
                'end_evn': data['end'],
                'week_evn': week,
                'department_id': department_id,
                'status_evn': status_evn,
                'list_chair_unit': list_chair_unit,
                'date_list_evn': date_list_evn,
                'calender_evn': calender_evn,
                'duid': department_id
            }
        else:
            group_list =  [i['group_id'] for i in group]
            # print(group_list)
            week = convertNumberWeek(date)
            status = check_Calender(date, department_id)
            # print(status)
            calender = getCalender(department_id, date)
            date_list = dateOfWeek(department_id, date)
            status_draf = status
            calender_draf = getCalender_draf(date, '0')
            date_list_draf = dateOfWeek_draf(date, '0')
            list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
            context = {
                'date': date,
                'start': data['start'],
                'end': data['end'],
                'week': week,
                'department_name': department[0]['department_name'],
                'group': group,
                'group_list': group_list,
                'status': status,
                'date_list': date_list,
                'calender': calender,
                'date_draf': date,
                'start_draf': data['start'],
                'end_draf': data['end'],
                'week_draf': week,
                'department_id': department_id,
                'status_draf': status_draf,
                'list_chair_unit': list_chair_unit,
                'date_list_draf': date_list_draf,
                'calender_draf': calender_draf,
                'duid': department_id
            }
        print(context)
        if 3 in group_list:
            print("calender/letter_draft.html")
            return render(request, "calender/letter_draft.html", context)
        else:
            return render(request, "calender/body.html", context)

def start_end_of_week(date):
    today = datetime.strptime(date, '%d-%m-%Y').date()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    # print(today)
    # print(start)
    # print(end)
    return {
        'start': start.strftime('%d-%m-%Y'),
        'end': end.strftime('%d-%m-%Y')
    }

def convertDate(date):
    dmy = datetime.strptime(date, '%d-%m-%Y')
    ymd = dmy.strftime('%Y-%m-%d')
    return ymd

def getDepartment(uid):
    sql = "select au.*, cp.department_id, upper(de.name) department_name, de.PB as parent_id from auth_user au inner join calender_profile cp on au.id = cp.user_id inner join calender_department de on cp.department_id = de.id and au.id = %s"
    data = connect_sql(sql, uid)
    return data

def dateOfWeek(idd, date):
    date_list = []
    today = datetime.strptime(date, '%d-%m-%Y').date()
    start = today - timedelta(days=today.weekday())
    # Tính thứ, ngày từ loop for of the week
    for i in range(7):
        item = {}
        dmy = start + timedelta(days=i)
        d = dmy.strftime('%d-%m-%Y')
        ymd = dmy.strftime('%Y-%m-%d')
        item['date'] = d
        item['day'] = week(dmy.strftime('%A'))

        sqlc = """select CONVERT(VARCHAR(10), start_time, 105) as date, week, count(CONVERT(VARCHAR(10), start_time, 105)) as count 
            from calender_calender cc inner join calender_department cd on cc.chair_unit_id= cd.id where status <> 'DONE' and create_depart_id_id = %s and 
            CONVERT(VARCHAR(10), start_time, 21) = %s
            group by week, CONVERT(VARCHAR(10), start_time, 105)"""
        count = connect_sql(sqlc, idd, ymd)
        # print(count)
        item['count'] = count[0]['count'] if len(count)>0 else 0
        date_list.append(item)
    # print(date_list)
    return date_list

def dateOfWeek_draf(date, chair_unit_id):
    date_list = []
    today = datetime.strptime(date, '%d-%m-%Y').date()
    start = today - timedelta(days=today.weekday())
    # Tính thứ, ngày từ loop for of the week
    for i in range(7):
        item = {}
        dmy = start + timedelta(days=i)
        d = dmy.strftime('%d-%m-%Y')
        ymd = dmy.strftime('%Y-%m-%d')
        item['date'] = d
        item['day'] = week(dmy.strftime('%A'))

        if chair_unit_id == "0":
            sql = """select CONVERT(VARCHAR(10), start_time, 105) as date, week, count(CONVERT(VARCHAR(10), start_time, 105)) as count 
                from calender_calender cc inner join calender_department cd on cc.chair_unit_id= cd.id where status <> 'DONE' and 
                CONVERT(VARCHAR(10), start_time, 21) = %s
                group by week, CONVERT(VARCHAR(10), start_time, 105)"""
            count = connect_sql(sql, ymd)
        else:
            sql = """select CONVERT(VARCHAR(10), start_time, 105) as date, week, count(CONVERT(VARCHAR(10), start_time, 105)) as count 
                from calender_calender cc inner join calender_department cd on cc.chair_unit_id= cd.id where cc.create_depart_id_id = %s and status <> 'DONE' and 
                CONVERT(VARCHAR(10), start_time, 21) = %s
                group by week, CONVERT(VARCHAR(10), start_time, 105)"""
            count = connect_sql(sql, chair_unit_id, ymd)
        # print(count)
        item['count'] = count[0]['count'] if len(count)>0 else 0
        date_list.append(item)
    # print(date_list)
    return date_list

def getGroupUserId(uid):
    sql = "select group_id from auth_user_groups where user_id = %s"
    data = connect_sql(sql, uid)
    return data

def getDepartmentUserId(uid):
    sql = "select department_id from calender_profile where user_id = %s"
    data = connect_sql(sql, uid)
    return data

def getCalender(idd, date):
    date_obj = start_end_of_week(date)
    start = convertDate(date_obj['start'])
    end = addOneDate(date_obj['end'])
    end = convertDate(end)
    sql = """select CONVERT(VARCHAR(10), start_time, 105) as date, CONVERT(VARCHAR(5), start_time, 108) as starttime, CONVERT(VARCHAR(5), end_time, 108) as endtime, cc.*, cd.name, coalesce(cm.name, '') as meeting_name, ROW_NUMBER() OVER (
    PARTITION BY CONVERT(VARCHAR(10), start_time, 105)
    ORDER BY CONVERT(VARCHAR(5), start_time, 108)
    ) row_num from calender_calender cc
    inner join calender_department cd on cc.chair_unit_id= cd.id 
    left join calender_meeting cm on cc.location_id = cm.id
    where status <> 'DONE' and create_depart_id_id = %s and start_time between %s and %s order by start_time asc"""
    data = connect_sql(sql, idd, start, end)
    # print(data)
    if data:
        for i in data:
            sql_joins = """select cd.id, cd.name from calender_department cd inner join calender_joincomponent cjc on cd.id = cjc.department_id where cjc.calender_id = %s"""
            rs_joins = connect_sql(sql_joins, i['id'])
            sql_prepares = """select cd.id, cpu.department_id, cd.name from calender_department cd inner join calender_prepareunit cpu on cd.id = cpu.department_id where cpu.calender_id = %s"""
            rs_prepares = connect_sql(sql_prepares, i['id'])
            sql_files = """select id, files, create_date from calender_multiplefile where calendar_id = %s and files != ''"""
            rs_files = connect_sql(sql_files, i['id'])
            item_join = [ j['name'] for j in rs_joins if j['id']]
            item_prepare = [ p['name'] for p in rs_prepares if p['id']]
            item_files = [ (m['id'], m['files'], m['create_date'],) for m in rs_files if m['id']]
            i['join_component'] = item_join
            i['prepare_unit'] = item_prepare       
            i['multi_file'] = item_files        
    # print(data)
    return data

def getCalender_draf(date, chair_unit_id):
    date_obj = start_end_of_week(date)
    start = convertDate(date_obj['start'])
    end = addOneDate(date_obj['end'])
    end = convertDate(end)
    #print('chair_unit_id: ', chair_unit_id)
    if chair_unit_id == "0":
        sql = """select CONVERT(VARCHAR(10), start_time, 105) as date, CONVERT(VARCHAR(5), start_time, 108) as starttime, CONVERT(VARCHAR(5), end_time, 108) as endtime, cc.*, cd.name, coalesce(cm.name, '') as meeting_name, ROW_NUMBER() OVER (
                PARTITION BY CONVERT(VARCHAR(10), start_time, 105)
                ORDER BY CONVERT(VARCHAR(5), start_time, 108)
                ) row_num from calender_calender cc
                inner join calender_department cd on cc.chair_unit_id= cd.id 
                left join calender_meeting cm on cc.location_id = cm.id
                where status <> 'DONE' and start_time between %s and %s order by start_time asc"""
        data = connect_sql(sql, start, end)
    else:
        sql = """select CONVERT(VARCHAR(10), start_time, 105) as date, CONVERT(VARCHAR(5), start_time, 108) as starttime, CONVERT(VARCHAR(5), end_time, 108) as endtime, cc.*, cd.name, coalesce(cm.name, '') as meeting_name, ROW_NUMBER() OVER (
                PARTITION BY CONVERT(VARCHAR(10), start_time, 105)
                ORDER BY CONVERT(VARCHAR(5), start_time, 108)
                ) row_num from calender_calender cc
                inner join calender_department cd on cc.chair_unit_id= cd.id 
                left join calender_meeting cm on cc.location_id = cm.id
                where cc.create_depart_id_id = %s and status <> 'DONE' and start_time between %s and %s order by start_time asc"""
        data = connect_sql(sql, chair_unit_id, start, end)
    # print(data)
    if data:
        for i in data:
            sql_joins = """select cd.id, cd.name from calender_department cd inner join calender_joincomponent cjc on cd.id = cjc.department_id where cjc.calender_id = %s"""
            rs_joins = connect_sql(sql_joins, i['id'])
            sql_prepares = """select cd.id, cpu.department_id, cd.name from calender_department cd inner join calender_prepareunit cpu on cd.id = cpu.department_id where cpu.calender_id = %s"""
            rs_prepares = connect_sql(sql_prepares, i['id'])
            sql_files = """select id, files, create_date from calender_multiplefile where calendar_id = %s and files != ''"""
            rs_files = connect_sql(sql_files, i['id'])
            item_join = [ j['name'] for j in rs_joins if j['id']]
            item_prepare = [ p['name'] for p in rs_prepares if p['id']]
            item_files = [ (m['id'], m['files'], m['create_date'],) for m in rs_files if m['id']]
            i['join_component'] = item_join
            i['prepare_unit'] = item_prepare
            i['multi_file'] = item_files
    return data

def week(name):
    switcher={
        'Monday':'Thứ hai',
        'Tuesday':'Thứ ba',
        'Wednesday':'Thứ tư',
        'Thursday':'Thứ năm',
        'Friday':'Thứ sáu',
        'Saturday':'Thứ bảy',
        'Sunday':'Chủ nhật'
    }
    return switcher.get(name, "Invalid day of week")

def addOneDate(date):
    today = datetime.strptime(date, '%d-%m-%Y').date()
    # start = today - timedelta(days=today.weekday())
    tomorrow = today + timedelta(days=1)
    # print('tomorrow: ', tomorrow)
    return tomorrow.strftime('%d-%m-%Y')

def convertNumberWeek(date):
    p = datetime.strptime(date, '%d-%m-%Y')
    return int(p.strftime("%V"))

@method_decorator(never_cache, name='dispatch')
class Login(View):
    def get(self, request):
        return render(request, "calender/login.html")
    
    def post(self, request):
        if request.method == 'POST':
            address = os.environ.get("AUTH_LDAP_SERVER_URI")
            domain = os.environ.get("DOMAIN")
            user_password = os.environ.get("PASSWORD")
            print('ip: ', address)
            username = request.POST.get('username')
            password = request.POST.get('password')
            # Authenticate with LDAP
            ldap = ldap_test.authenticate(address, domain, username, password)
            # print('result: ', ldap)
            # user_auth = authenticate(username=username, password=password)          # APPLY FOR DEVELOPMENT
            user_auth = authenticate(username=username, password=user_password)
            # print(user_auth)
            # print(username)
            # if user_auth:                 # APPLY FOR DEVELOPMENT
            if user_auth and ldap:   
            # Redirecting to the required login according to user status.
                if user_auth.is_active:
                    if user_auth.is_superuser or user_auth.is_staff:
                        login(request, user_auth)
                        if "lichxe" in request.path:
                            return redirect('/admin/vehicle/vehiclecalender/')  
                        else:
                            return redirect('/admin/calender/calender')  
                    else:
                        return render(request, "calender/login.html", {'alert': 'Tài khoản của bạn chưa được kích hoạt. Vui lòng liên hệ quản trị viên.'})
                else:
                    # login(request, user)
                    return render(request, "calender/login.html", {'alert': 'Tài khoản của bạn chưa được kích hoạt. Vui lòng liên hệ quản trị viên.'})
            else:
                return render(request, "calender/login.html", {'alert': 'Bạn hãy nhập đúng Tên tài khoản và mật khẩu. (Có phân biệt chữ hoa, thường)'})


def check_calender_letter(date, department_id):
    week = convertNumberWeek(date)
    year = date.split('-')[-1]          # Get last element of list
    check_calender = 'DONE'
    if department_id == "0":
        sql = "select status from calender_calender where week = %s and YEAR(start_time) = %s"
        data = connect_sql(sql, week, year)
    else:
        sql = "select status from calender_calender where week = %s and YEAR(start_time) = %s and create_depart_id_id = %s"
        data = connect_sql(sql, week, year, department_id)
        # print("data: ", data)
    if len(data) == 0:
        return 'NONE'
    else:
        for item in data:
            if item['status'] == 'NEW':
                return 'NEW'
        if department_id == "0":
            sql2 = "select check_calender_letter from calender_calender where status <> 'NEW' and week = %s and YEAR(start_time) = %s"
            data2 = connect_sql(sql2, week, year)
        else:
            sql2 = "select check_calender_letter from calender_calender where status <> 'NEW' and week = %s and YEAR(start_time) = %s and create_depart_id_id = %s"
            data2 = connect_sql(sql2, week, year, department_id)
        for e in data2:
            if e['check_calender_letter'] == False:
                return 'ACCEPT'
    return check_calender

def get_calender_type(date, chair_unit_id, status):
    date_obj = start_end_of_week(date)
    start = convertDate(date_obj['start'])
    end = addOneDate(date_obj['end'])
    end = convertDate(end)
    # bugsnag.notify(Exception('Test error'))
    #print(type(date_obj))
    if status == 'draft':
        if chair_unit_id == "0":
            sql = """select CONVERT(VARCHAR(10), start_time, 105) as date, CONVERT(VARCHAR(5), start_time, 108) as starttime, CONVERT(VARCHAR(5), end_time, 108) as endtime, cc.*, cd.name, coalesce(cm.name, '') as meeting_name, ROW_NUMBER() OVER (
            PARTITION BY CONVERT(VARCHAR(10), start_time, 105)
            ORDER BY CONVERT(VARCHAR(5), start_time, 108)
            ) row_num from calender_calender cc
            inner join calender_department cd on cc.chair_unit_id= cd.id 
            left join calender_meeting cm on cc.location_id = cm.id
            where status in ('NEW', 'ACCEPT') and start_time between %s and %s order by start_time asc"""
            data = connect_sql(sql, start, end)
        else:
            sql = """select CONVERT(VARCHAR(10), start_time, 105) as date, CONVERT(VARCHAR(5), start_time, 108) as starttime, CONVERT(VARCHAR(5), end_time, 108) as endtime, cc.*, cd.name, coalesce(cm.name, '') as meeting_name, ROW_NUMBER() OVER (
            PARTITION BY CONVERT(VARCHAR(10), start_time, 105)
            ORDER BY CONVERT(VARCHAR(5), start_time, 108)
            ) row_num from calender_calender cc
            inner join calender_department cd on cc.chair_unit_id= cd.id 
            left join calender_meeting cm on cc.location_id = cm.id
            where create_depart_id_id = %s and status in ('NEW', 'ACCEPT') and start_time between %s and %s order by start_time asc"""
            data = connect_sql(sql, chair_unit_id, start, end)
    if status == 'approval':
        if chair_unit_id == "0":
            sql = """select CONVERT(VARCHAR(10), start_time, 105) as date, CONVERT(VARCHAR(5), start_time, 108) as starttime, CONVERT(VARCHAR(5), end_time, 108) as endtime, cc.*, cd.name, coalesce(cm.name, '') as meeting_name, ROW_NUMBER() OVER (
            PARTITION BY CONVERT(VARCHAR(10), start_time, 105)
            ORDER BY CONVERT(VARCHAR(5), start_time, 108)
            ) row_num from calender_calender cc
            inner join calender_department cd on cc.chair_unit_id= cd.id 
            left join calender_meeting cm on cc.location_id = cm.id
            where status in ('DONE') and start_time between %s and %s order by start_time asc"""
            data = connect_sql(sql, start, end)
        else:
            result = medium_query(chair_unit_id, start, end)
            # print('result: ', result)
            ids_calender = tuple([i['id'] for i in result])
            # item_placeholders = ', '.join(['{}'] * len(ids_calender))
            # print(item_placeholders)
            # Nếu tuple length equal 1 (number, ) thì bỏ dấu phẩy
            if len(ids_calender)==1:
                ids_calender = 'cc.id in {} and'.format('(%s)' % ', '.join(map(repr, ids_calender)))
            elif len(ids_calender)>1:
                ids_calender = 'cc.id in {} and'.format(ids_calender)
            else:
                ids_calender = 'cc.id = 0 and'
            # print('ids_calender: ', ids_calender)
            # print('ids_calender type: ', type(ids_calender))
            sql = """select CONVERT(VARCHAR(10), start_time, 105) as date, CONVERT(VARCHAR(5), start_time, 108) as starttime, CONVERT(VARCHAR(5), end_time, 108) as endtime, cc.*, cd.name, coalesce(cm.name, '') as meeting_name, ROW_NUMBER() OVER (
            PARTITION BY CONVERT(VARCHAR(10), start_time, 105)
            ORDER BY CONVERT(VARCHAR(5), start_time, 108)
            ) row_num from calender_calender cc
            inner join calender_department cd on cc.chair_unit_id= cd.id 
            left join calender_meeting cm on cc.location_id = cm.id
            where {} status in ('DONE') and start_time between '{}' and '{}' order by start_time asc""".format(ids_calender, start, end)
            data = connect_sql(sql)
    if status == 'draft-company':
        if chair_unit_id == "0":
            sql = """select CONVERT(VARCHAR(10), start_time, 105) as date, CONVERT(VARCHAR(5), start_time, 108) as starttime, CONVERT(VARCHAR(5), end_time, 108) as endtime, cc.*, cd.name, coalesce(cm.name, '') as meeting_name, ROW_NUMBER() OVER (
            PARTITION BY CONVERT(VARCHAR(10), start_time, 105)
            ORDER BY CONVERT(VARCHAR(5), start_time, 108)
            ) row_num from calender_calender cc
            inner join calender_department cd on cc.chair_unit_id= cd.id 
            left join calender_meeting cm on cc.location_id = cm.id
            where status in ('ACCEPT', 'DONE') and start_time between %s and %s order by start_time asc"""
            data = connect_sql(sql, start, end)
        else:
            sql = """select CONVERT(VARCHAR(10), start_time, 105) as date, CONVERT(VARCHAR(5), start_time, 108) as starttime, CONVERT(VARCHAR(5), end_time, 108) as endtime, cc.*, cd.name, coalesce(cm.name, '') as meeting_name, ROW_NUMBER() OVER (
            PARTITION BY CONVERT(VARCHAR(10), start_time, 105)
            ORDER BY CONVERT(VARCHAR(5), start_time, 108)
            ) row_num from calender_calender cc
            inner join calender_department cd on cc.chair_unit_id= cd.id 
            left join calender_meeting cm on cc.location_id = cm.id
            where create_depart_id_id = %s and status in ('ACCEPT', 'DONE') and start_time between %s and %s order by start_time asc"""
            data = connect_sql(sql, chair_unit_id, start, end)

    # print('date_obj[start]:', type(date_obj['start']))
    # print('date_obj[end]:', date_obj['end'])
    # print(date)
    # print(data)
    if data:
        for i in data:
            #sql_joins = """select cd.id, cd.name from calender_department cd inner join calender_joincomponent cjc on cd.id = cjc.department_id where cjc.calender_id = %s"""
            sql_joins = """select cd.id, cd.name from calender_department cd inner join calender_calender cjc on cd.id = cjc.chair_unit_id where cjc.id = %s"""
            rs_joins = connect_sql(sql_joins, i['id'])
            sql_prepares = """select cd.id, cpu.department_id, cd.name from calender_department cd inner join calender_prepareunit cpu on cd.id = cpu.department_id where cpu.calender_id = %s"""
            rs_prepares = connect_sql(sql_prepares, i['id'])
            sql_files = """select id, files, create_date from calender_multiplefile where calendar_id = %s and files != ''"""
            rs_files = connect_sql(sql_files, i['id'])
            sql_division = """select cwd.user_id, u.first_name, u.last_name, u.username, cd.name from calender_working_division as cwd inner join (select user_id, first_name, last_name, username, department_id from auth_user au inner join calender_profile cp on au.id = cp.user_id) u on u.user_id = cwd.user_id
                left join calender_department cd on cd.id = u.department_id where cwd.active = 1 and cwd.calender_id = %s"""
            rs_division = connect_sql(sql_division, i['id'])
            item_join = [ j['name'] for j in rs_joins if j['id']]
            item_join_ids = [ j['id'] for j in rs_joins if j['id']]
            item_prepare = [ p['name'] for p in rs_prepares if p['id']]
            ids_prepare = [ p['department_id'] for p in rs_prepares if p['department_id']]
            item_files = [ (m['id'], m['files'], m['create_date'],) for m in rs_files if m['id']]
            #print('item: ', item_join)
            i['join_component'] = item_join
            i['join_component_ids'] = item_join_ids
            i['prepare_unit'] = item_prepare
            i['prepare_unit_ids'] = ids_prepare
            i['multi_file'] = item_files
            i['division_list'] = acronym_depart(rs_division)
            # print("rs_division: %s" %(rs_division))
            i['filter_group'] = group_by_depart(rs_division)
            # print(i['filter_group'])
    # print(data)
    return data

def dateOfWeek_type(date, chair_unit_id, status):
    date_list = []
    today = datetime.strptime(date, '%d-%m-%Y').date()
    start = today - timedelta(days=today.weekday())
    # Tính thứ, ngày từ loop for of the week
    for i in range(7):
        item = {}
        dmy = start + timedelta(days=i)
        d = dmy.strftime('%d-%m-%Y')
        ymd = dmy.strftime('%Y-%m-%d')
        # BEGIN Bổ sung để lọc theo ĐVCT, TPTG, ĐVCB
        end = start + timedelta(days=i+1)
        end_ymd = end.strftime('%Y-%m-%d')
        # END Bổ sung để lọc theo ĐVCT, TPTG, ĐVCB
        item['date'] = d
        item['day'] = week(dmy.strftime('%A'))
        if status == 'draft':
            if chair_unit_id == "0":
                sqlc = """select CONVERT(VARCHAR(10), start_time, 105) as date, week, count(CONVERT(VARCHAR(10), start_time, 105)) as count 
                    from calender_calender cc inner join calender_department cd on cc.chair_unit_id= cd.id where status in ('NEW', 'ACCEPT') and
                    CONVERT(VARCHAR(10), start_time, 21) = %s
                    group by week, CONVERT(VARCHAR(10), start_time, 105)"""
                count = connect_sql(sqlc, ymd)
            else:
                sqlc = """select CONVERT(VARCHAR(10), start_time, 105) as date, week, count(CONVERT(VARCHAR(10), start_time, 105)) as count 
                    from calender_calender cc inner join calender_department cd on cc.chair_unit_id= cd.id where status in ('NEW', 'ACCEPT') and
                    CONVERT(VARCHAR(10), start_time, 21) = %s
                    and cc.create_depart_id_id = %s
                    group by week, CONVERT(VARCHAR(10), start_time, 105)"""
                count = connect_sql(sqlc, ymd, chair_unit_id)
        if status == 'approval':
            if chair_unit_id == "0":
                sqlc = """select CONVERT(VARCHAR(10), start_time, 105) as date, week, count(CONVERT(VARCHAR(10), start_time, 105)) as count 
                    from calender_calender cc inner join calender_department cd on cc.chair_unit_id= cd.id where status in ('DONE') and
                    CONVERT(VARCHAR(10), start_time, 21) = %s
                    group by week, CONVERT(VARCHAR(10), start_time, 105)"""
                # print('sqlc: {}'.format(sqlc))
                # print('ymd: {}'.format(ymd))
                count = connect_sql(sqlc, ymd)
            else:
                result = medium_query(chair_unit_id, ymd, end_ymd)
                # print('result of week: ', result)
                ids_calender = tuple([i['id'] for i in result])
                # Nếu tuple length equal 1 (number, ) thì bỏ dấu phẩy
                if len(ids_calender)==1:
                    ids_calender = 'and cc.id in {}'.format('(%s)' % ', '.join(map(repr, ids_calender)))
                elif len(ids_calender)>1:
                    ids_calender = 'and cc.id in {}'.format(ids_calender)
                else:
                    ids_calender = 'and cc.id = {}'.format(0)
                # print('ids_calenderssssssssssssss: ', ids_calender)
                sqlc = """select CONVERT(VARCHAR(10), start_time, 105) as date, week, count(CONVERT(VARCHAR(10), start_time, 105)) as count 
                    from calender_calender cc inner join calender_department cd on cc.chair_unit_id= cd.id where status in ('DONE') and
                    CONVERT(VARCHAR(10), start_time, 21) = '{}'
                    {}
                    group by week, CONVERT(VARCHAR(10), start_time, 105)""".format(ymd, ids_calender)
                count = connect_sql(sqlc)
        if status == 'draft-company':
            if chair_unit_id == "0":
                sqlc = """select CONVERT(VARCHAR(10), start_time, 105) as date, week, count(CONVERT(VARCHAR(10), start_time, 105)) as count 
                    from calender_calender cc inner join calender_department cd on cc.chair_unit_id= cd.id where status in ('ACCEPT', 'DONE') and
                    CONVERT(VARCHAR(10), start_time, 21) = %s
                    group by week, CONVERT(VARCHAR(10), start_time, 105)"""
                count = connect_sql(sqlc, ymd)
            else:
                sqlc = """select CONVERT(VARCHAR(10), start_time, 105) as date, week, count(CONVERT(VARCHAR(10), start_time, 105)) as count 
                    from calender_calender cc inner join calender_department cd on cc.chair_unit_id= cd.id where status in ('ACCEPT', 'DONE') and
                    CONVERT(VARCHAR(10), start_time, 21) = %s
                    and cc.create_depart_id_id = %s
                    group by week, CONVERT(VARCHAR(10), start_time, 105)"""
                count = connect_sql(sqlc, ymd, chair_unit_id)
                
        # print(count)
        item['count'] = count[0]['count'] if len(count)>0 else 0
        date_list.append(item)
    # print(date_list)
    return date_list

def depart_draft(request):
    if request.method == "POST": 
        date = request.POST['date']
        state = request.POST['status']
        chair_unit_id = request.POST['value']
        data = start_end_of_week(date)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        group = getGroupUserId(user_id)
        # print('grouppppppppppppp re-render: ', group)
        group_list = [i['group_id'] for i in group]
        week = convertNumberWeek(date)
        status = check_calender_letter(date, chair_unit_id)
        # print("check_calender_letter state DEP: ", status)
        # calender = getCalender_draf(date, chair_unit_id)
        # date_list = dateOfWeek_draf(date, chair_unit_id)
        calender = get_calender_type(date, chair_unit_id, state)
        date_list = dateOfWeek_type(date, chair_unit_id, state)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'status': status,
            'week': week,
            'group': group,
            'department_id': chair_unit_id,
            'date_list': date_list,
            'calender': calender,
            'group_list': group_list,
            'list_chair_unit': list_chair_unit
        }
        return render(request, "calender/department_draft.html", context)

def company_draft(request):
    if request.method == "POST": 
        # print("postttttttttttttttttttttttt company_draft")
        date = request.POST['date']
        state = request.POST['status']
        chair_unit_id = request.POST['value']
        data = start_end_of_week(date)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        group = getGroupUserId(user_id)
        # print('grouppppppppppppp re-render: ', group)
        group_list = [i['group_id'] for i in group]
        week = convertNumberWeek(date)
        status_evn = check_calender_letter(date, chair_unit_id)
        # print("check_calender_letter state: ", status_evn)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        # calender = getCalender_draf(date, chair_unit_id)
        # date_list = dateOfWeek_draf(date, chair_unit_id)
        calender = get_calender_type(date, chair_unit_id, state)
        date_list = dateOfWeek_type(date, chair_unit_id, state)
        context = {
            'date_evn': date,
            'start_evn': data['start'],
            'end_evn': data['end'],
            'status_evn': status_evn,
            'week_evn': week,
            'list_chair_unit': list_chair_unit,
            'department_id': chair_unit_id,
            'date_list_evn': date_list,
            'calender_evn': calender,
            'group_list': group_list,
            'duid': department_id
        }
        return render(request, "calender/company_draft.html", context)

def approval_draft_com(request):
    # print("approval_draft_com")
    if request.method == 'POST':
        data_string = request.POST.get('json_data')
        data_dict = json.loads(data_string)
        date = data_dict['info']['date']
        state = data_dict['info']['status']
        chair_unit_id = data_dict['info']['chair_unit_id']
        listIdCalender = data_dict['info']['listIdCalender']
        listIdCalender_notCheck = data_dict['info']['listIdCalender_notCheck']
        
        data = start_end_of_week(date)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        week = convertNumberWeek(date)

        for item in listIdCalender:
            sql = "UPDATE calender_calender SET check_calender_letter=1, status='DONE', write_date = %s WHERE id = %s"
            execute_sql(sql, datetime.now(), item)
            # INSER LOG TO QNaPC_ChangeToChat
            calendar_item = CalenderModel.objects.get(id=item)
            id_status = calendar_item.cancel_status    # QUERYSET IS AWESOME
            valid_time = calendar_item.start_time
            if id_status in [2, 3, 4] and valid_time >= datetime.now():      # [CHANGE, ADDITIONAL, UNEXPECTED]
                insert_chat = "INSERT INTO QNaPC_ChangeToChat(id, id_pb, username, sended, send_time, cancel_status, write_date, user_edit)  VALUES (%s, NULL, NULL, 0, NULL, %s, %s, %s)"
                execute_sql(insert_chat, item, id_status, datetime.now(), user_id)

        for item in listIdCalender_notCheck:
            sql2 = "UPDATE calender_calender SET check_calender_letter=0, status='ACCEPT', write_date = %s WHERE id = %s"
            execute_sql(sql2, datetime.now(), item)

        status = check_calender_letter(date, chair_unit_id)
        # print(state)

        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        # calender = getCalender_draf(date, chair_unit_id)
        # date_list = dateOfWeek_draf(date, chair_unit_id)
        calender = get_calender_type(date, chair_unit_id, state)
        date_list = dateOfWeek_type(date, chair_unit_id, state)
        context = {
            'date_evn': date,
            'start_evn': data['start'],
            'end_evn': data['end'],
            'status_evn': status,
            'week_evn': week,
            'list_chair_unit': list_chair_unit,
            'department_id': chair_unit_id,
            'date_list_evn': date_list,
            'calender_evn': calender,
            'group_list': group_list,
            'duid': department_id
        }
        return render(request, "calender/company_draft.html", context)

def cancel_approval_draft_com(request):
    # print("cancel_approval_draft_com")
    if request.method == 'POST':
        data_string = request.POST.get('json_data')
        data_dict = json.loads(data_string)
        date = data_dict['info']['date']
        state = data_dict['info']['status']
        chair_unit_id = data_dict['info']['chair_unit_id']
        listIdCalender = data_dict['info']['listIdCalender']

        data = start_end_of_week(date)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        week = convertNumberWeek(date)
        for item in listIdCalender:
            sql = "UPDATE calender_calender SET check_calender_letter=0, status='ACCEPT', write_date = %s WHERE id = %s"
            execute_sql(sql, datetime.now(), item)
        
        status = check_calender_letter(date, chair_unit_id)
        # print(status)
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        # calender = getCalender(department_id, start)
        # date_list = dateOfWeek(department_id, start)
        calender = get_calender_type(date, chair_unit_id, state)
        date_list = dateOfWeek_type(date, chair_unit_id, state)
        context = {
            'date_evn': date,
            'week_evn': week,
            'start_evn': data['start'],
            'end_evn': data['end'],
            'department_id': department_id,
            'department_name': department[0]['department_name'],
            'list_chair_unit': list_chair_unit,
            'group': group,
            'status_evn': status,
            'date_list_evn': date_list,
            'calender_evn': calender,
            'group_list': group_list,
            'duid': department_id
        }
        return render(request, "calender/company_draft.html", context)


def approval_draft_dep(request):
    # print("approval_draft_dep")
    if request.method == 'POST':
        data_string = request.POST.get('json_data')
        data_dict = json.loads(data_string)
        date = data_dict['info']['date']
        state = data_dict['info']['status']
        chair_unit_id = data_dict['info']['chair_unit_id']
        listIdCalender = data_dict['info']['listIdCalender']
        listIdCalender_notCheck = data_dict['info']['listIdCalender_notCheck']
        
        data = start_end_of_week(date)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        week = convertNumberWeek(date)

        for item in listIdCalender:
            sql = "UPDATE calender_calender SET check_calender=1, status='ACCEPT', write_date = %s WHERE id = %s"
            execute_sql(sql, datetime.now(), item)

        for item in listIdCalender_notCheck:
            sql2 = "UPDATE calender_calender SET check_calender=0, status='NEW', write_date = %s WHERE id = %s"
            execute_sql(sql2, datetime.now(), item)

        status = check_calender_letter(date, chair_unit_id)

        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        # calender = getCalender_draf(date, chair_unit_id)
        # date_list = dateOfWeek_draf(date, chair_unit_id)
        calender = get_calender_type(date, chair_unit_id, state)
        date_list = dateOfWeek_type(date, chair_unit_id, state)
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'status': status,
            'week': week,
            'list_chair_unit': list_chair_unit,
            'department_id': chair_unit_id,
            'department_name': department[0]['department_name'],
            'group': group,
            'group_list': group_list,
            'date_list': date_list,
            'calender': calender
        }
        return render(request, "calender/department_draft.html", context)

def cancel_approval_draft_dep(request):
    # print("cancel_approval_draft_dep")
    if request.method == 'POST':
        data_string = request.POST.get('json_data')
        data_dict = json.loads(data_string)
        date = data_dict['info']['date']
        state = data_dict['info']['status']
        listIdCalender = data_dict['info']['listIdCalender']
        chair_unit_id = data_dict['info']['chair_unit_id']
        data = start_end_of_week(date)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        week = convertNumberWeek(date)
        for item in listIdCalender:
            sql = "UPDATE calender_calender SET check_calender=0, status='NEW', write_date = %s WHERE id = %s"
            execute_sql(sql, datetime.now(), item)
        
        status = check_calender_letter(date, chair_unit_id)
        # print(status)
        
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        # calender = getCalender(department_id, start)
        # date_list = dateOfWeek(department_id, start)
        calender = get_calender_type(date, chair_unit_id, state)
        date_list = dateOfWeek_type(date, chair_unit_id, state)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        context = {
            'date': date,
            'week': week,
            'start': data['start'],
            'end': data['end'],
            'department_id': chair_unit_id,
            'department_name': department[0]['department_name'],
            'group': group,
            'group_list': group_list,
            'status': status,
            'date_list': date_list,
            'calender': calender,
            'list_chair_unit': list_chair_unit
        }
        return render(request, "calender/department_draft.html", context)

def expected_list(date):
    week = convertNumberWeek(date)
    year = date.split('-')[-1]          # Get last element of list
    next_week = week + 1
    # print('next_week: ', next_week)
    # expected_list = ExpectedCalender.objects.filter(week=next_week)
    sql = "select content from calender_expectedcalender where week = %s and YEAR(create_date) = %s"
    expected_list = connect_sql(sql, next_week, year)
    # print(expected_list)
    return expected_list

# Re-render calendar of company
def filter_type(request):
    if request.method == "POST":
        date = request.POST['start']
        #date = '25-05-2020'
        chair_unit_id = request.POST['value']
        status = request.POST['status']
        # print(date)
        # print(chair_unit_id)
        data = start_end_of_week(date)
        user_id = request.user.pk
        department_id = getDepartment(user_id)[0]['department_id']
        parent_id = getDepartment(user_id)[0]['parent_id']
        # print('department_id: ', department_id)
        week = convertNumberWeek(date)
        # print('status: ', status)
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        getDepart = getDepartmentUserId(user_id)
        list_users = getlistusers(getDepart[0]['department_id'])
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        calender = get_calender_type(date, chair_unit_id, status)
        date_list = dateOfWeek_type(date, chair_unit_id, status)
        # print(calender)
        # print(date_list)
        expectedlist = expected_list(date)
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'week': week,
            'chair_unit_id': chair_unit_id,
            'list_chair_unit': list_chair_unit,
            'date_list': date_list,
            'calender': calender,
            'group_list': group_list,
            'list_users': list_users,
            'expected_list': expectedlist,
            'department_id': department_id,
            'parent_id': parent_id
        }
        return render(request, "calender/approval.html", context)

# Nếu xuất excel ở lịch dự thảo công ty thì sẽ export theo hai status 'ACCEPT' & 'DONE'
def get_date(date, department_id, status):
    # print("get_date date: ", date)
    # print("get_date department_id: ", department_id)
    # print("get_date status: ", status)
    date_data = start_end_of_week(date)
    week = convertNumberWeek(date)
    # status = getCalenderStatus_vt(week)
    #print(status)
    calender = get_calender_type(date, department_id, status)
    date_list = dateOfWeek_type(date, department_id, status)
    expectedlist = expected_list(date)
    context = {
        'date': date,
        'start': date_data['start'],
        'end': date_data['end'],
        'week': week,
        'date_list': date_list,
        'calender': calender,
        'expected_list': expectedlist
    }
    return context

def confirmDelete(request):
    # print("confirmDeleteeeeeeeeeee")
    if request.method == "POST":
        date = request.POST['date']
        idcalender = request.POST['idcalender']
        
        # Deleting media file in store system directory
        sql_file = "select files from calender_multiplefile where calendar_id = %s and files != ''"
        file_list = connect_sql(sql_file, idcalender)

        # print('files_list: ', len(file_list))
        if len(file_list) > 0:
            for f in file_list:
                path = settings.MEDIA_ROOT + "\\" + f['files']
                # print('path: ', path)
                exist = os.path.exists(path)
                if exist:
                    os.remove(path)

        sql = "delete calender_joincomponent where calender_id = %s"
        execute_sql(sql, idcalender)
        
        sql = "delete calender_prepareunit where calender_id = %s"
        execute_sql(sql, idcalender)
        
        sql = "delete calender_multiplefile where calendar_id = %s"
        execute_sql(sql, idcalender)
        
        sql = "delete calender_calender where id = %s"
        execute_sql(sql, idcalender)
        data = start_end_of_week(date)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        group = getGroupUserId(user_id)
        # print('grouppppppppppppp re-render: ', group)
        group_list = [i['group_id'] for i in group]
        week = convertNumberWeek(date)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')

        if 3 in group_list:
            state = 'draft'
            status = check_calender_letter(date, department_id)
            # print("check_calender_letter state DEP: ", status)
            calender = get_calender_type(date, department_id, state)
            date_list = dateOfWeek_type(date, department_id, state)
            formrender = "calender/department_draft.html"
        else:
            status = check_Calender(date, department_id)
            calender = getCalender(department_id, date)
            date_list = dateOfWeek(department_id, date)
            formrender = "calender/reload.html"
            
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'status': status,
            'week': week,
            'group': group,
            'department_id': department_id,
            'department_name': department[0]['department_name'],
            'date_list': date_list,
            'calender': calender,
            'group_list': group_list,
            'list_chair_unit': list_chair_unit
        }
        return render(request, formrender, context)


class ListCreateExpectedView(ListCreateAPIView):
    model = ExpectedCalender
    serializer_class = ExpectedSerialize

    def get_queryset(self):
        week = self.request.query_params.get('week')
        queryset = ExpectedCalender.objects.filter(week=week)
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        # data = JSONParser().parse(request)
        # print(data)
        # print(type(data))
        # data['create_uid'] = request.user
        serializer = ExpectedSerialize(data=data)
        # print('serializer: ', serializer)
        if serializer.is_valid():
            # print('serializer.is_valid(): ', serializer.is_valid())
            serializer.save()
            return JsonResponse({
                'message': 'Tạo lịch dự kiến thành công!'
            }, status=status.HTTP_201_CREATED)
        
        return JsonResponse({
            'message': 'Tạo lịch dự kiến thất bại!'
        }, status=status.HTTP_400_BAD_REQUEST)


class UpdateDeleteExpectedView(RetrieveUpdateDestroyAPIView):
    model = ExpectedCalender
    serializer_class = ExpectedSerialize

    def put(self, request, *args, **kwargs):
        expected = get_object_or_404(ExpectedCalender, id=kwargs.get('pk'))
        serializer = ExpectedSerialize(expected, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return JsonResponse({
                'message': 'Cập nhật thành công!'
            }, status=status.HTTP_200_OK)
        
        return JsonResponse({
                'message': 'Cập nhật thất bại!'
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        expected = get_object_or_404(ExpectedCalender, id=kwargs.get('pk'))
        expected.delete()

        return JsonResponse({
                'message': 'Xóa thành công!'
            }, status=status.HTTP_200_OK)

def confirmUpdateCalender(request):
    if request.method == "POST":
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        date = request.POST['date']
        idcalender = request.POST['idcalender']
        chair_unit_id = request.POST['value']
        sql_update = "update calender_calender set cancel_status = 1, slide_show = 0, write_date = %s where id = %s"
        execute_sql(sql_update, datetime.now(), idcalender)
        # INSER LOG TO QNaPC_ChangeToChat
        calendar_item = CalenderModel.objects.get(id=idcalender)
        id_status = calendar_item.cancel_status    # QUERYSET IS AWESOME
        valid_time = calendar_item.start_time
        if valid_time >= datetime.now():
            insert_chat = "INSERT INTO QNaPC_ChangeToChat(id, id_pb, username, sended, send_time, cancel_status, write_date, user_edit)  VALUES (%s, NULL, NULL, 0, NULL, %s, %s, %s)"
            execute_sql(insert_chat, idcalender, id_status, datetime.now(), user_id)
        data = start_end_of_week(date)
        week = convertNumberWeek(date)
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        getDepart = getDepartmentUserId(user_id)
        list_users = getlistusers(getDepart[0]['department_id'])
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        calender = get_calender_type(date, chair_unit_id, 'approval')
        date_list = dateOfWeek_type(date, chair_unit_id, 'approval')
        # print(calender)
        # print(date_list)
        expectedlist = expected_list(date)
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'week': week,
            'chair_unit_id': chair_unit_id,
            'list_chair_unit': list_chair_unit,
            'date_list': date_list,
            'calender': calender,
            'group_list': group_list,
            'list_users': list_users,
            'expected_list': expectedlist,
            'department_id': department_id
        }
        return render(request, "calender/data.html", context)

def confirmRecycleCalender(request):
    if request.method == "POST":
        date = request.POST['date']
        idcalender = request.POST['idcalender']
        chair_unit_id = request.POST['value']
        sql_update = "update calender_calender set cancel_status = 0, write_date = %s where id = %s"
        execute_sql(sql_update, datetime.now(), idcalender)
        data = start_end_of_week(date)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        week = convertNumberWeek(date)
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        getDepart = getDepartmentUserId(user_id)
        list_users = getlistusers(getDepart[0]['department_id'])
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        calender = get_calender_type(date, chair_unit_id, 'approval')
        date_list = dateOfWeek_type(date, chair_unit_id, 'approval')
        # print(calender)
        # print(date_list)
        expectedlist = expected_list(date)
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'week': week,
            'chair_unit_id': chair_unit_id,
            'list_chair_unit': list_chair_unit,
            'date_list': date_list,
            'calender': calender,
            'group_list': group_list,
            'list_users': list_users,
            'expected_list': expectedlist,
            'department_id': department_id
        }
        return render(request, "calender/data.html", context)

def medium_query(dep, date1, date2):
    sql = """select distinct cc.id from calender_calender cc 
			left join calender_joincomponent cj on cc.id = cj.calender_id
			left join calender_prepareunit cp on cc.id = cp.calender_id
			where status in ('DONE') 
			and ( cc.chair_unit_id = %s or cj.department_id = %s or cp.department_id = %s)
			and start_time between %s and %s """
    data = connect_sql(sql, dep, dep, dep, date1, date2)
    return data

def check_double_calender(request):
    if request.method == "POST":
        date1 = request.POST['date1']
        date1 = (datetime.strptime(date1, '%d-%m-%Y %H:%M')).strftime('%Y-%m-%d %H:%M')
        date2 = request.POST['date2']
        date2 = (datetime.strptime(date2, '%d-%m-%Y %H:%M')).strftime('%Y-%m-%d %H:%M')
        if request.POST['meeting_id']:
            meeting_id = request.POST['meeting_id']  
        chair_unit_id = request.POST['chair_unit_id']
        if chair_unit_id:
            sql_manager = "select id from calender_department where name like N'GĐPC%' or name like N'%PGĐ KD%' or name like N'%PGĐ KT%' or name like N'%PGĐ ĐTXD%'"
            # print("chair: ", chair_unit_id)
            result_manager = connect_sql(sql_manager)
            manager_ids = [i['id'] for i in result_manager]
            # print('manager_ids: ', manager_ids)
            if int(chair_unit_id) in manager_ids:
                # print("dddddddddddddddddddddddddddddddddddddddddddddddd")
                sql = """select start_time, end_time, location_id from calender_calender 
                    where chair_unit_id = %s and ( start_time >= %s and start_time <= %s or end_time >= %s 
                    and end_time <= %s or start_time <= %s and end_time >= %s)"""
                data = connect_sql(sql, chair_unit_id, date1, date2, date1, date2, date1, date2)
            else:
                data = None
        else:
            # print("elseeeeeeeeeeeeeeeeeeeeeeeee")
            sql = """select start_time, end_time, location_id from calender_calender 
                where location_id = %s and ( start_time >= %s and start_time <= %s or end_time >= %s 
                and end_time <= %s or start_time <= %s and end_time >= %s)"""
            data = connect_sql(sql, meeting_id, date1, date2, date1, date2, date1, date2)

        # print(date1)
        # print(date2)
        # print(meeting_id)
        # print(chair_unit_id)
        if data:
            return JsonResponse({
                'message': 'YES'
            }, status=status.HTTP_200_OK)
        else:
            return JsonResponse({
                'message': 'NO'
            }, status=status.HTTP_200_OK)

def on_off_slide_show(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        calendar_id = request.POST.get('calendar_id')
        depart_id = request.POST.get('depart_id')
        slide_show =request.POST.get('slide_show')

        if int(slide_show) == 0:
            sql = "update calender_calender set slide_show = {} where id = {}".format(int(slide_show), calendar_id)
            execute_sql(sql)
        else:
            sql = "update calender_calender set slide_show = {} where id = {}".format(int(slide_show), calendar_id)
            execute_sql(sql)

        user_id = request.user.pk
        department = getDepartment(user_id)
        chair_unit_id = department[0]['department_id']
        
        data = start_end_of_week(date)
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        week = convertNumberWeek(date)
        list_users = getlistusers(chair_unit_id)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        calender = get_calender_type(date, depart_id, 'approval')
        date_list = dateOfWeek_type(date, depart_id, 'approval')
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'week': week,
            'department_id': chair_unit_id,
            'list_chair_unit': list_chair_unit, 
            'group_list': group_list,
            'list_users': list_users,
            'date_list': date_list,
            'calender': calender
        }
        return render(request, "calender/data.html", context)

def confirmUndoBrowse(request):
    # print("confirmUndoBrowse")
    if request.method == 'POST':
        data_string = request.POST.get('json_data')
        data_dict = json.loads(data_string)
        date = data_dict['info']['date']
        state = data_dict['info']['status']
        chair_unit_id = data_dict['info']['chair_unit_id']
        idcalender = data_dict['info']['idcalender']
        
        data = start_end_of_week(date)
        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        week = convertNumberWeek(date)

        sql2 = "UPDATE calender_calender SET check_calender_letter=0, status='ACCEPT', write_date = %s WHERE id = %s"
        execute_sql(sql2, datetime.now(), idcalender)

        status = check_calender_letter(date, chair_unit_id)
        # print(state)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        # calender = getCalender_draf(date, chair_unit_id)
        # date_list = dateOfWeek_draf(date, chair_unit_id)
        calender = get_calender_type(date, chair_unit_id, state)
        date_list = dateOfWeek_type(date, chair_unit_id, state)
        context = {
            'date_evn': date,
            'start_evn': data['start'],
            'end_evn': data['end'],
            'status_evn': status,
            'week_evn': week,
            'list_chair_unit': list_chair_unit,
            'department_id': chair_unit_id,
            'date_list_evn': date_list,
            'calender_evn': calender,
            'group_list': group_list,
            'duid': department_id
        }
        return render(request, "calender/company_draft.html", context)

def get_user_permission_objects(user):
    if user.is_superuser:
        return Permission.objects.all()
    else:
        return Permission.objects.filter(Q(user=user) | Q(group__user=user)).distinct()

def create_expected(request):
    try:
        if request.method == "POST":
            user_id = request.user
            week = request.POST['week']
            content = request.POST['content']
            if user_id and int(week) and content:
                # print(user_id)
                # print(week)
                # print(content)
                data = ExpectedCalender(week=week, content=content, create_uid=user_id)
                data.save()
                return JsonResponse({
                    'message': 'Tạo lịch dự kiến thành công!'
                }, status=status.HTTP_201_CREATED) 
            return JsonResponse({
                'message': 'Vui lòng nhập đầy đủ thông tin!'
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return JsonResponse({
            'message': 'Vui lòng nhập đầy đủ thông tin!!'
        }, status=status.HTTP_400_BAD_REQUEST)

def check_status(calender_id, form):
    calendar = CalenderModel.objects.get(id=calender_id)
    # print('calendar.check_calender_letter: ', calendar.check_calender_letter)
    form_data = form.cleaned_data
    week = int(form_data['start_time'].strftime('%V'))
    if calendar.check_calender_letter:
        
        default_start_time = calendar.start_time.strftime('%Y-%m-%d %H:%M:%S')
        default_end_time = calendar.end_time.strftime('%Y-%m-%d %H:%M:%S')
        # print('default_start_time: ', default_start_time)
        # print('default_end_time: ', default_end_time)
        start_time = form_data['start_time'].strftime('%Y-%m-%d %H:%M:%S')
        end_time = form_data['end_time'].strftime('%Y-%m-%d %H:%M:%S')
        # print('start_time: ', start_time)
        # print('end_time: ', end_time)

        default_location = calendar.location_id
        default_address = calendar.address
        # print('default_location: ', default_location)
        # print('default_address: ', default_address)
        # print('location: ', form_data['location'].id)
        # print('address: ', form_data['address'])

        if form_data['location']:
            if default_location != form_data['location'].id:
                return week, 5

        if default_address != form_data['address']:
            return week, 5
        elif start_time != default_start_time or end_time != default_end_time:
            return week, 6
        else:
            return week, 2
    return week, None

def draftEdit(request, pk):
    print('tuanta5 test add lich')
    try:
        # print('pkkkkkkkkkkkkkk: ', pk)
        calendar = CalenderModel.objects.get(id=pk)
        # print('calendar: ', calendar)
        # permissions = Permission.objects.filter(user=request.user)
        
        permissions = get_user_permission_objects(request.user)
        user_perms = [x.id for x in permissions]
        # print('user_perms: ', user_perms)

        content_type = ContentType.objects.get_for_model(CalenderModel)
        all_permissions = [y.id for y in Permission.objects.filter(content_type=content_type)]
        # print('all_permissions: ', all_permissions)
        # form = CalenderChangeForm(request.POST)
        creater = User.objects.get(id=calendar.create_uid.id).last_name
        department = Department.objects.get(id=calendar.create_depart_id_id).name
        if request.method == 'POST':
            form = CalenderChangeForm(request.POST, instance=calendar)
            disableform = DisableForm(initial={'creater': creater, 'department': department})
            formset = FileFormSet(request.POST, request.FILES, instance=calendar)
            # print('form.is_valid(): ', form.is_valid())
            # print('formset.is_valid(): ', formset.is_valid())
            # print('cleaned_data[start]: ', form.cleaned_data['start_time'])
            # print('cleaned_data[end]: ', form.cleaned_data['end_time'])
            # print('form errors: ', form.errors.as_data())
            if form.is_valid() and formset.is_valid():
                if form.has_changed():
                    # data = form.save(commit=False)
                    response_status = check_status(pk, form)
                    update_query_manual(pk, form)
                    # print(response_status)
                    # Nếu status != None thì update lịch ban hành
                    # Còn không thì update week lịch dự thảo
                    if response_status[1] != None:
                        CalenderModel.objects.filter(id=pk).update(week=response_status[0], cancel_status=response_status[1], write_date=datetime.now())  
                        valid_time = calendar.start_time
                        if valid_time >= datetime.now():
                            insert_chat = "INSERT INTO QNaPC_ChangeToChat(id, id_pb, username, sended, send_time, cancel_status, write_date, user_edit)  VALUES (%s, NULL, NULL, 0, NULL, %s, %s, %s)"
                            execute_sql(insert_chat, pk, response_status[1], datetime.now(), request.user.pk)   # Change time
                    else:
                        CalenderModel.objects.filter(id=pk).update(week=response_status[0], write_date=datetime.now())  
                    # print('cleaned_data: ', form.cleaned_data)
                formset.save()
                return HttpResponseRedirect('/admin/calender/draft')
        else:
            if calendar.start_time >= datetime.now():
                form = CalenderChangeForm(instance=calendar)
            else:
                form = CalenderChangeForm(instance=calendar)
                for fieldname in form.fields:
                    form.fields[fieldname].disabled = True
                
            disableform = DisableForm(initial={'creater': creater, 'department': department})
            formset = FileFormSet(instance=calendar)
            # print(formset)
        context = {
            'form': form,
            'disableform': disableform,
            'formset': formset
        }
        return render(request, 'calender/calender_edit.html', context)
    except Exception as exc:
        print(exc)
        return HttpResponseRedirect('/admin/calender/draft')

# SHOULD BE USE CLASS BASED VIEWS INSTEAD OF CLASS BASED VIEWS
class CalenderList(ListView):
    model = Calender
    template_name = 'calender/calender_edit2.html'
    # queryset = Calender.objects.all()


class CalenderDetailView(DetailView):
    template_name = 'calender/calender_detail.html'
    # queryset = Department.objects.all()
    model = Calender

    def get_object(self):
        id_ = self.kwargs.get("id")
        print(id_)
        print(CalenderModel.objects.get(id=id_))
        print('get_object_or_404: ', get_object_or_404(CalenderModel, id=id_))
        return get_object_or_404(CalenderModel, id=id_)


class CalenderCreateView(CreateView):
    model = CalenderModel
    form_class = CalenderChangeForm
    # formset_class = FileForm
    template_name = 'calender/calender_add.html'
    success_url = '/'

    def form_valid(self, form):
        print('formmmmmmmmmmmmmmmm:')
        form.save()
        formset.save()
        return super().form_valid(form)
    
    def form_invalid(self, form):
        print('form.cleaned_data: ', form.cleaned_data)
        print('form.errors: ', form.errors.as_data())
        return self.render_to_response(
        self.get_context_data(form=form.errors))

    # def get_success_url(self, *args, **kwargs):
    #     return reverse("/admin")

    # def get(self, request, *args, **kwargs):
    #     """
    #     Handles GET requests and instantiates blank version of the form
    #     and its inline formsets.
    #     """
    #     self.object = self.get_object()
    #     form_class = self.get_form_class()
    #     form = self.get_form(form_class)

    #     # Get areas
    #     areas = CalenderModel.objects.get(id=self.object)

    #     # Render form
    #     area_form = CalenderFormSet(instance=areas)
    #     return self.render_to_response(
    #         self.get_context_data(form=form,
    #                             area_form = area_form))

    def get_context_data(self, **kwargs):
        context = super(CalenderCreateView, self).get_context_data(**kwargs)
        context['form'] = CalenderChangeForm()
        context['formset'] = FileForm()
        return context

    # def get_object(self):
    #     context = {}
    #     id_ = self.kwargs.get("id")
    #     files = CalenderModel.objects.get(id=id_)
    #     print(id_)
    #     print(CalenderModel.objects.get(id=id_))
    #     print('get_object_or_404: ', type(get_object_or_404(CalenderModel, id=id_)))
    #     # context['form'] = CalenderModel.objects.get(id=id_)
    #     # context['form_files'] = CalenderFormSet(instance=files)
    #     return get_object_or_404(CalenderModel, id=id_)

def reload_confirm_division(req_user, date, chair_unit_id, status="approval"):
    try:
        data = start_end_of_week(date)
        user_id = req_user.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id']
        parent_id = department[0]['parent_id']
        # print('department_id: ', department_id)
        week = convertNumberWeek(date)
        # print('status: ', status)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        group = getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        getDepart = getDepartmentUserId(user_id)
        list_users = getlistusers(getDepart[0]['department_id'])
        calender = get_calender_type(date, chair_unit_id, status)
        date_list = dateOfWeek_type(date, chair_unit_id, status)
        context = {
            'date': date,
            'start': data['start'],
            'end': data['end'],
            'week': week,
            'chair_unit_id': chair_unit_id,
            'list_chair_unit': list_chair_unit, 
            'group_list': group_list,
            'list_users': list_users,
            'date_list': date_list,
            'calender': calender,
            'department_id': department_id,
            'parent_id': parent_id
        }
        return context
        # render(request, "calender/data.html", context)
    except Exception as exc:
        print(exc)
        return None

def confirm_division(request):
    try:
        if request.method == 'POST':
            user_id = request.user.pk
            data_string = request.POST.get('json_data')
            # Convert string dict into json dict by loads()
            data_dict = json.loads(data_string)
            calender_id = data_dict["calender_id"]
            users_check = data_dict["users_check"]
            users_no_check = data_dict["users_no_check"]
            date = data_dict["date"]
            selected_depart = data_dict["chair_unit_id"]
            # If user do not exist in db then INSERT 2 table, otherwise then UPDATE
            for user in users_check:
                # filter() can use id and get() must be instance of class
                if Working_Division.objects.filter(calender=calender_id, user=int(user)).exists() == False:
                    # print("======INSERT=============")
                    insert = Working_Division(calender=CalenderModel.objects.get(id=calender_id), user=User.objects.get(id=user), active=True, create_uid=request.user)
                    insert.save()
                    # insert_msg = "INSERT INTO QNaPC_PhanCongLich(username, id_lich, thoigian_phancong, sended)  VALUES (%d, %d, '%s', %d)" % (int(user), int(calender_id), datetime.now(), 0)
                    # print(insert_msg)
                    # execute_sql(insert_msg)
                else:
                    # print("======UPDATE==============")
                    Working_Division.objects.filter(calender=calender_id, user=int(user)).update(active=True, write_uid=user_id, write_date=datetime.now())  
            # If user that not check exists in db then update active
            for user in users_no_check:
                if Working_Division.objects.filter(calender=calender_id, user=int(user)).exists() == True:
                    # print("==================UPDATE NO ACTIVE===================")
                    Working_Division.objects.filter(calender=calender_id, user=int(user)).update(active=False, write_uid=user_id, write_date=datetime.now())  
            
            context = reload_confirm_division(request, date, selected_depart)
            if context != None:
                return render(request, "calender/data.html", context)
            else:
                return HttpResponse("false")

    except Exception as exc:
        print(exc)
        return HttpResponse("false")

# Tên phòng ban viết tắt
def acronym_depart(lst):
    result = []
    for dep in lst:
        if "name" in dep:
            item_list = dep["name"].split(" ")
            name = ""
            for i, e in enumerate(item_list):
                # If department name has this keywords then cut it, 
                # after get 1 character and convert accented into unsigned
                if e not in ["phòng", "Phòng"] and len(e) > 0:
                    name = name + no_accent(str(e[0])).upper()
            # dep["name"] = name
        if dep["last_name"] != "":
            dep["last_name"] = dep["last_name"].split("(")[0].strip()
        result.append(dep)
    return result

def no_accent(s):
    s = s.lower()
    s = re.sub('[áàảãạăắằẳẵặâấầẩẫậ]', 'a', s)
    s = re.sub('[éèẻẽẹêếềểễệ]', 'e', s)
    s = re.sub('[óòỏõọôốồổỗộơớờởỡợ]', 'o', s)
    s = re.sub('[íìỉĩị]', 'i', s)
    s = re.sub('[úùủũụưứừửữự]', 'u', s)
    s = re.sub('[ýỳỷỹỵ]', 'y', s)
    # s = re.sub('đ', 'd', s)
    return s

def group_by_depart(user_list):
    dep = [user['name'] for user in user_list if user['name'] not in user_list]
    result = []
    for de in set(dep):
        obj = {}
        users = []
        obj['name'] = de
        for ur in user_list:
            if ur['name'] == de:
                users.append(ur['last_name']) if ur['last_name'] else users.append(ur['username'])
        obj['user'] = users
        result.append(obj)
    # [{'name': 'BQLDA', 'user': ['Phạm Văn Hồng', 'Lê Văn Thái', 'Lê Ngọc Trường']},...]
    final_result = []
    for i in result:
        urs = ", ".join(i['user'])
        #final_result.append("<b>" + i['name'] + "</b>" + " (" + urs + ")")
        final_result.append("" + urs + "")
    return final_result
    # BQLDA(Phạm Văn Hồng, Lê Văn Thái, Lê Ngọc Trường)
    # ...

def update_query_manual(pk, form):
    try:
        # Get all changed fields in form and compare 
        change_fields = form.changed_data
        if 'join_component' in change_fields:
            sql = "delete calender_joincomponent where calender_id = %s"
            execute_sql(sql, pk)
            for join in form.cleaned_data['join_component']:
                sql_insert = "insert into calender_joincomponent(calender_id, department_id) values(%s, %s)"
                execute_sql(sql_insert, pk, str(join.id))
        if 'prepare_unit' in change_fields:
            sql = "delete calender_prepareunit where calender_id = %s"
            execute_sql(sql, pk)
            for unit in form.cleaned_data['prepare_unit']:
                sql_insert = "insert into calender_prepareunit(calender_id, department_id) values(%s, %s)"
                execute_sql(sql_insert, pk, str(unit.id))
        # print(change_fields)
        str_field = ""
        params = []
        # Target of for loop is get 2 value to fill the query below without ['join_component', 'prepare_unit']
        for field in change_fields:
            if field in ['join_component', 'prepare_unit']:
                continue
            field_name = field if field not in ['location', 'chair_unit'] else field + "_id"        # special case _id
            str_field += field_name + " = %s,"
            if field in ['start_time', 'end_time']:
                params.append("'%s'" % (form.cleaned_data[field]))
            if field in ['location', 'chair_unit']:
                if form.cleaned_data[field]:
                    params.append(form.cleaned_data[field].id)
                else:
                    params.append('null')
            if field in ['address', 'join_quantity', 'content', 'other_requirements', 'other_component', 'other_prepare']:
                if form.cleaned_data[field]:
                    params.append("N'%s'" % (form.cleaned_data[field]))
                else:
                    params.append('null')
            if field in ['requirement1', 'requirement2', 'requirement3', 'requirement4', 'requirement5']:
                params.append(1 if form.cleaned_data[field]==True else 0)

        # print(sql % tuple(params))
        if len(str_field) > 0 and len(params) > 0:
            sql = "UPDATE calender_calender SET " + str_field[:-1] + " WHERE id = " + str(pk)       # so complex
            execute_sql(sql % tuple(params))
        return True
    except Exception as exc:
        print(exc)
        return False