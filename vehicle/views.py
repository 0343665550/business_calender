from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime, timedelta
from django.views import View
from django.http import HttpResponse
from django.views.generic import DetailView
from calender.views import connect_sql, start_end_of_week, addOneDate, convertDate, week, convertNumberWeek, getGroupUserId, no_accent
from calender.models import *
from .models import VehicleCalender as ModelVehicleCalender, Vehicle, Vehicle_Division, Driver_Division
from .forms import CalenderUpdateDetailForm, CalenderDisableForm, CalenderAddForm
import json, logging, xlsxwriter
from django.contrib.auth.models import User
# Create your views here.

# Saving error logs in file "vehicle_log"
def LoggingFile(msg):
     #set different formats for logging output
    # console_logging_format = '%(levelname)s:&amp;nbsp; %(message)s'
    file_logging_format = '%(levelname)s: %(asctime)s: %(message)s'
    
    # configure logger
    logging.basicConfig(level=logging.DEBUG, format=file_logging_format)
    logger = logging.getLogger()
    # create a file handler for output file
    handler = logging.FileHandler('vehicle_file.log')
    
    # set the logging level for log file
    handler.setLevel(logging.INFO)
    # create a logging format
    formatter = logging.Formatter(file_logging_format)
    handler.setFormatter(formatter)
    
    # add the handlers to the logger
    logger.addHandler(handler)

    logger.error(msg)
    return

# Cutting user name, only get name without (...)
def cut_name(item):
    if '(' in item['last_name']:
        item['last_name'] = item['last_name'].split("(")[0].strip()
    return item

# Tên phòng ban viết tắt
def acronym_depart(lst):
    result = []
    for dep in lst:
        if "dep_name" in dep:
            item_list = dep["dep_name"].split(" ")
            name = ""
            if len(item_list) > 1:
                for i, e in enumerate(item_list):
                    # after get 1 character and convert accented into unsigned
                    name = name + no_accent(str(e[0])).upper()
                dep["dep_name"] = name
            elif len(item_list) == 1:
                dep["dep_name"] = item_list[0]
        result.append(dep)
    return result

def error_action(request):
    return render(request, "vehicle/500_ISE.html")

def sql_calender_detail(date, departmt, is_left_tab, status="ALL"):
    try:
        date_obj = start_end_of_week(date)
        start = convertDate(date_obj['start'])
        _end = addOneDate(date_obj['end'])
        end = convertDate(_end)
        stats = ""
        if status == "ALL":
            stats = ""
        else:
            stats = "and status in ('%s')" % status
        department = ""
        if departmt != '0':
            department = "and vvc.register_unit_id = %s" % departmt
        if is_left_tab == True:        # is left tab display
            # is_left = "select * from vehicle_vehicletype where is_left_tab = 1"
            vhc_type = "vt.is_left_tab = 1"
        else:
            vhc_type = "vt.is_left_tab = 0"
        sql_main ="""select CONVERT(VARCHAR(10), start_time, 105) as date, CONVERT(VARCHAR(5), start_time, 108) as starttime, CONVERT(VARCHAR(5), end_time, 108) as endtime, 
            vvc.*, cd.name as register_unit_name, au.last_name, vt.name, ROW_NUMBER() OVER (
            PARTITION BY CONVERT(VARCHAR(10), start_time, 105)
            ORDER BY CONVERT(VARCHAR(5), start_time, 108)
            ) row_num from vehicle_vehiclecalender vvc
            inner join calender_department cd on vvc.register_unit_id = cd.id 
            inner join auth_user au on vvc.create_uid_id = au.id
            inner join vehicle_vehicletype vt on vvc.vehicle_type_id = vt.id
            where %s %s %s and start_time between '%s' and '%s' order by start_time asc"""
        # print("======================sql_main=============================")
        # print(sql_main % (vhc_type, stats, department, start, end))
        data_list = connect_sql(sql_main % (vhc_type, stats, department, start, end))
        for item in data_list:
            sql_vehicle = """select vd.vehicle_id, v.name, cd.name as dep_name, v.number from vehicle_vehicle_division as vd inner join vehicle_vehicle as v on v.id = vd.vehicle_id
                inner join calender_department as cd on v.manage_unit_id = cd.id
                where vd.active = 1 and vd.calender_id = %s"""
            rs_vehicle = connect_sql(sql_vehicle, item["id"])
            sql_driver = """select user_id, first_name, last_name, username, dep_name from vehicle_driver_division as dd 
                inner join (select user_id, first_name, last_name, username, cd.name as dep_name, cp.is_driver from auth_user au inner join calender_profile cp on au.id = cp.user_id inner join calender_department cd on cp.department_id = cd.id) 
                u on u.user_id = dd.driver_id
                where u.is_driver = 1 and dd.active = 1 and dd.calender_id = %s"""
            rs_driver = connect_sql(sql_driver, item["id"])

            item["vehicles"] = acronym_depart(rs_vehicle)
            item["drivers"] = acronym_depart(list(map(cut_name, rs_driver)))        # Cut ...(...) name is behind
        # print("===========================data_list=================================")
        # print(data_list)
        return data_list
    except Exception as exc:
        print(exc)
        LoggingFile(exc)
        return None

def date_of_week(date, departmt, is_left_tab, status="ALL"):
    try:
        date_list = []
        date_select = datetime.strptime(date, '%d-%m-%Y').date()
        start = date_select - timedelta(days=date_select.weekday())
        department = ""
        stats = ""
        if status == "ALL":
            stats = ""
        else:
            stats = "and status in ('%s')" % status
        if departmt != '0':
            department = "and vc.register_unit_id = %s" % departmt
        if is_left_tab == True:        # is left tab display
            # is_left = "select * from vehicle_vehicletype where is_left_tab = 1"
            vhc_type = "and vt.is_left_tab = 1"
        else:
            vhc_type = "and vt.is_left_tab = 0"
        # print("DEBUGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG")
        # Tính thứ, ngày từ loop for of the week begin 0=>6
        for i in range(7):
            item = {}
            dmy = start + timedelta(days=i)         
            dmy_str = dmy.strftime('%d-%m-%Y')
            ymd_str = dmy.strftime('%Y-%m-%d')
            item['date'] = dmy_str
            item['day'] = week(dmy.strftime('%A'))

            sql_every_day = """select CONVERT(VARCHAR(10), start_time, 105) as date, week, count(CONVERT(VARCHAR(10), start_time, 105)) as count 
                from vehicle_vehiclecalender vc inner join calender_department cd on vc.register_unit_id = cd.id 
                inner join vehicle_vehicletype vt on vc.vehicle_type_id = vt.id 
                where CONVERT(VARCHAR(10), start_time, 21) = '%s' %s %s %s
                group by week, CONVERT(VARCHAR(10), start_time, 105)"""
            # print(sql_every_day % (ymd_str, vhc_type, department, stats))
            count = connect_sql(sql_every_day % (ymd_str, vhc_type, department, stats))

            item['count'] = count[0]['count'] if len(count)>0 else 0
            date_list.append(item)
        # print("===========================date_list=================================")
        # print(date_list)
        return date_list
    except Exception as exc:
        print(exc)
        LoggingFile(exc)
        return None


class VehicleCalender(View):
    def get(self, request):
        try:
            # GET PARAMETER LIST FROM GET METHOD
            date_left = request.GET['d1']
            depa_left = request.GET['r1']
            stat_left = request.GET['s1']
            date_right = request.GET['d2']
            depa_right = request.GET['r2']
            stat_right = request.GET['s2']
            tab_active = request.GET['tab_active']

            data = start_end_of_week(date_left)
            data_right = start_end_of_week(date_right)

            user_id = request.user.pk
            groups = getGroupUserId(user_id)
            user_group_list = [i['group_id'] for i in groups]

            week = convertNumberWeek(date_left)
            week_right = convertNumberWeek(date_right)
            status_list = ModelVehicleCalender.STATUS
            register_unit_list = Department.objects.filter(active=True, is_vehicle_calender=True).order_by('group', 'sequence')
            calender_list = sql_calender_detail(date_left, depa_left, True, stat_left)
            date_list = date_of_week(date_left, depa_left, True, stat_left)
            # =================TAB TO THE RIGHT=================
            calender_list_right = sql_calender_detail(date_right, depa_right, False, stat_right)
            date_list_right = date_of_week(date_right, depa_right, False, stat_right)
            # ============================PERMISIONS=============================
            has_perm_add = request.user.has_perm("vehicle.register_vehicle")
            has_perm_confirm = request.user.has_perm("vehicle.confirm_vehicle")
            has_perm_approval = request.user.has_perm("vehicle.approval_vehicle")
            has_perm_assign = request.user.has_perm("vehicle.assign_vehicle")
            
            context = {
                'tab_active': tab_active,
                'date': date_left,
                'date_right': date_right,
                'start': data['start'],
                'end': data['end'],
                'start_right': data_right['start'],
                'end_right': data_right['end'],
                'week': week,
                'week_right': week_right,
                'status_id': stat_left,
                'status_id_right': stat_right,
                'unit_id': depa_left,
                'unit_id_right': depa_right,
                'register_unit_list': register_unit_list,
                'status_list': status_list,
                'date_list': date_list,
                'date_list_right': date_list_right,
                'calender_list': calender_list,
                'calender_list_right': calender_list_right,
                'user_group_list': user_group_list,
                'has_perm_add': has_perm_add,
                'has_perm_confirm': has_perm_confirm,
                'has_perm_approval': has_perm_approval,
                'has_perm_assign': has_perm_assign
            }
            # print(date_left, depa_left, stat_left)
            # print(date_right, depa_right, stat_right)
            return render(request, "vehicle/index.html", context)
        except Exception as exc:
            print(exc)
            LoggingFile(exc)
            return redirect('/vehicle/unexpected_error/')

    def post(self, request):    # DIVISION VEHICLE
        try:
            user_id = request.user
            str_data = request.POST.get('json_data')
            json_data = json.loads(str_data)
            # print("--------------------------------str_data----------------------------------")
            # print(str_data)
            cid = json_data['calender_id']
            note = json_data['note']
            vehicle_list = json_data['vehicle_list']
            driver_list = json_data['driver_list']

            vehicle_list_db = [str(v.vehicle.id) for v in Vehicle_Division.objects.filter(calender=cid)]
            s = set(vehicle_list)
            s_db = set(vehicle_list_db)
            # Use DIFFERENCE SET to comparision 2 set
            compare = s_db - s
            if len(compare) > 0:
                for veh in compare:
                    Vehicle_Division.objects.filter(calender=cid, vehicle=int(veh)).update(active=False, write_uid=user_id, write_date=datetime.now())  
            # If drivers in database that more than selected list then update active by false
            driver_list_db = [str(d.driver.id) for d in Driver_Division.objects.filter(calender=cid)]
            set_drivers = set(driver_list)
            set_drivers_db = set(driver_list_db)
            compare_driver = set_drivers_db - set_drivers
            if len(compare_driver) > 0:
                for drv in compare_driver:
                    Driver_Division.objects.filter(calender=cid, driver=int(drv)).update(active=False, write_uid=user_id, write_date=datetime.now())
            
            ModelVehicleCalender.objects.filter(id=cid).update(note=note, status="ASSIGNED", write_uid=user_id, write_date=datetime.now())
            # ==============UPDATE VEHICLE LIST====================
            for veh in vehicle_list:
                if Vehicle_Division.objects.filter(calender=cid, vehicle=veh).exists():
                    Vehicle_Division.objects.filter(calender=cid, vehicle=int(veh)).update(active=True, write_uid=user_id, write_date=datetime.now())  
                else:
                    insert = Vehicle_Division(calender=ModelVehicleCalender.objects.get(id=cid), vehicle=Vehicle.objects.get(id=veh), active=True, create_uid=user_id)
                    insert.save()
            # ==============UPDATE DRIVER LIST====================
            for drv in driver_list:
                if Driver_Division.objects.filter(calender=cid, driver=drv).exists():
                    Driver_Division.objects.filter(calender=cid, driver=int(drv)).update(active=True, write_uid=user_id, write_date=datetime.now())
                else:
                    insert = Driver_Division(calender=ModelVehicleCalender.objects.get(id=cid), driver=User.objects.get(id=drv), active=True, create_uid=user_id)
                    insert.save()
            return HttpResponse("true")
        except Exception as exc:
            print(exc)
            LoggingFile(exc)
            return HttpResponse("false")


def update_detail_view(request, cid):
    try:
        calender = ModelVehicleCalender.objects.get(id=cid)
        register = User.objects.get(id=calender.create_uid.id).last_name or User.objects.get(id=calender.create_uid.id).username
        register_unit = Department.objects.get(id=calender.register_unit.id).name
        # if calender.approved_by:
        #     profile_id = calender.approved_by.id
        #     user_id = Profile.objects.get(id=calender.approved_by.id).user_id
        #     print(user_id)
        approved_by = User.objects.get(id=calender.approved_by.id).last_name if calender.approved_by else '' \
            or User.objects.get(id=calender.approved_by.id).username if calender.approved_by else '' 

        has_perm_assign = request.user.has_perm("vehicle.assign_vehicle")
        # print(calender, register, register_unit)
        if request.method == 'POST':
            form = CalenderUpdateDetailForm(request.POST, instance=calender)
            # disableform = CalenderDisableForm(initial={
            #     'register': register, 
            #     'register_unit': register_unit, 
            #     'approved_by': calender.approved_by
            # })
            print("form error :", form.errors.as_data())
            if form.is_valid() and form.has_changed():
                #  and form.has_changed()
                post = form.save(commit=False)
                post.week = int(form.cleaned_data['start_time'].strftime("%V"))
                post.write_uid = request.user
                post.write_date = datetime.now()
                post.save()
                # print("form error :", form.errors.as_data())

                return redirect('/admin/vehicle/vehiclecalender/')
        else:
            if calender.start_time >= datetime.now() and request.user.has_perm("vehicle.assign_vehicle"):
                form = CalenderUpdateDetailForm(instance=calender)
            else:
                form = CalenderUpdateDetailForm(instance=calender)
                for fieldname in form.fields:
                    form.fields[fieldname].disabled = True
        disableform = CalenderDisableForm(initial={
            'register': register, 
            'register_unit': register_unit,
            'approved_by': approved_by
            # 'approved_by': Profile.objects.filter(user=calender.approved_by.id).values_list('user__last_name', flat=True)[0]
        })
        context = {
            'form': form,
            'disableform': disableform,
            'has_perm_assign': has_perm_assign
        }
        return render(request, "vehicle/calender_update_detail_view.html", context)
    except Exception as exc:
        print(exc)
        LoggingFile(exc)
        return redirect('/vehicle/unexpected_error/')

def add_view(request):
    try:
        if request.method == 'POST':
            form = CalenderAddForm(request.POST)
            # print(form.cleaned_data)
            if form.is_valid():
                post = form.save(commit=False)
                if request.user.has_perm("vehicle.confirm_vehicle"):
                    post.status = "CONFIRM"
                post.week = int(form.cleaned_data['start_time'].strftime("%V"))
                print(form.cleaned_data)
                if form.cleaned_data['approved_by_']:
                    post.approved_by = User.objects.get(id=form.cleaned_data['approved_by_'].user_id)
                    print(post.approved_by)
                # post.register = request.user
                post.create_uid = request.user
                register_unit = Profile.objects.get(user=request.user).department_id
                post.register_unit = Department.objects.get(id=register_unit)   # RESULT IS AN INSTANCE
                post.create_date = datetime.now()
                post.save()
                return redirect('/admin/vehicle/vehiclecalender/')
            # print("form error :", form.errors.as_data())
        else:
            form = CalenderAddForm(initial={ 'vehicle_type': 1 })

        context = {
            'form': form
        }
        return render(request, "vehicle/calender_add.html", context)
    except Exception as exc:
        print(exc)
        LoggingFile(exc)
        return redirect('/vehicle/unexpected_error/')

def confirm_action(request):
    try:
        if request.method == 'POST':
            cid = request.POST['calender_id']
            status = request.POST['status']
            # print(cid, status)
            if status == "NEW":
                ModelVehicleCalender.objects.filter(id=cid, status="NEW").update(status="CONFIRM")
                return HttpResponse("true")
            else:
                return HttpResponse("false")

    except Exception as exc:
        print(exc)
        return HttpResponse("false")

def approval_action(request):
    try:
        if request.method == 'POST':
            json_data = request.POST.get('json_data')
            cid_list = json.loads(json_data)['cid_list']
            user_id = request.user.pk
            prohibited_calendar = []
            for cal in cid_list:
                calendar = ModelVehicleCalender.objects.get(id=int(cal))
                if calendar.is_appr_manager and user_id != calendar.approved_by.id:
                    prohibited_calendar.append({
                        "content": calendar.content
                    })
                    continue
                ModelVehicleCalender.objects.filter(id=int(cal), status="CONFIRM").update(status="APPROVAL")
            if len(prohibited_calendar) == 0:
                return HttpResponse("true")
            else:
                return HttpResponse(json.dumps(prohibited_calendar))
    except Exception as exc:
        print(exc)
        return HttpResponse("false")

def info_modal_division(request, cid):
    try:
        sql_main = """
            select CONVERT(VARCHAR(10), start_time, 105) as date, CONVERT(VARCHAR(5), start_time, 108) as starttime, CONVERT(VARCHAR(5), end_time, 108) as endtime, 
            vvc.*, cd.name as register_unit_name, au.last_name, vt.name from vehicle_vehiclecalender vvc
            inner join calender_department cd on vvc.register_unit_id = cd.id 
            inner join auth_user au on vvc.create_uid_id = au.id
            inner join vehicle_vehicletype vt on vvc.vehicle_type_id = vt.id
            where vvc.id = %s"""
        detail_data = connect_sql(sql_main % cid)

        for item in detail_data:
            sql_vehicle = """select vd.vehicle_id, v.name from vehicle_vehicle_division as vd inner join vehicle_vehicle as v on v.id = vd.vehicle_id
                where vd.active = 1 and vd.calender_id = %s"""
            rs_vehicle = connect_sql(sql_vehicle, item["id"])
            sql_driver = """select user_id, first_name, last_name, username from vehicle_driver_division as dd 
                inner join (select user_id, first_name, last_name, username, cp.is_driver from auth_user au inner join calender_profile cp on au.id = cp.user_id) 
                u on u.user_id = dd.driver_id where u.is_driver = 1 and dd.active = 1 and dd.calender_id = %s"""
            rs_driver = connect_sql(sql_driver, item["id"])

            item["vehicles"] = rs_vehicle
            item["drivers"] = list(map(cut_name, rs_driver))
            # print("==========================vehicle_type=================================")
            # print(item['vehicle_type_id'])
            # ====================INFO MAIN TO DISPLAY MODAL========================
            # If need manage unit then add "manage_unit=item['create_uid_id']"
            vehicle_all = Vehicle.objects.filter(vehicle_type=item['vehicle_type_id'])
            item["vehicle_list"] = vehicle_all
            # sql_driver_all = "select id, username, last_name from auth_user where is_active = 1 and id in (select user_id from calender_profile where is_driver = 1)"
            sql_driver_all = """select au.id, au.username, au.last_name, cd.name as dep_name from auth_user au inner join calender_profile cp 
                on au.id = cp.user_id inner join calender_department cd on cp.department_id = cd.id
                where cp.is_driver = 1 and au.is_active = 1"""
            driver_all = connect_sql(sql_driver_all)
            item["driver_list"] = driver_all
        context = {
            'j': detail_data[0] if len(detail_data)>0 else {}
        }
        # print(context)
        return render(request, "vehicle/division_modal_view.html", context)
    except Exception as exc:
        print(exc)
        LoggingFile(exc)

# http://localhost:8000/vehicle/export_xlsx/?date=26-11-2020&depart_id=0&status=ALL&tab_active=left
def export_xlsx(request):
    if request.method == "GET" and request.user.pk:
        date = request.GET['date']
        depart_id = request.GET['depart_id'] or "0"
        state = request.GET['status']
        tab_active = request.GET['tab_active']
        arr_date = datetime.now().strftime('%d-%m-%Y').split("-")
        # print(date)
        data = excel_data(date, depart_id, tab_active, state)
        # print('data: ', data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = "attachment; filename=lichxe%s.xlsx" %("con" if tab_active=='left' else "cau")
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
        format_justify.set_align('center')
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
        if tab_active == 'left':
            worksheet.print_area('A1:I20')
        elif tab_active == 'right':
            worksheet.print_area('A1:K20')
        worksheet.fit_to_pages(1, 0)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)

        # Set width column
        worksheet.set_column(6, 0, 13)
        worksheet.set_column(6, 1, 22)
        worksheet.set_column(6, 2, 10)
        worksheet.set_column(6, 3, 15)
        worksheet.set_column(6, 4, 35)
        worksheet.set_column(6, 5, 20)
        
        if tab_active == 'left':
            worksheet.set_column(6, 6, 30)
            worksheet.set_column(6, 7, 30)
            worksheet.set_column(6, 8, 15)
        elif tab_active == 'right':
            worksheet.set_column(6, 6, 30)
            worksheet.set_column(6, 7, 15)
            worksheet.set_column(6, 8, 10)
            worksheet.set_column(6, 9, 30)
            worksheet.set_column(6, 10, 15)

        worksheet.merge_range('A2:K2', 'TỔNG CÔNG TY ĐIỆN LỰC MIỀN TRUNG', format1)
        worksheet.merge_range('A3:K3', 'CÔNG TY ĐIỆN LỰC QUẢNG NAM', format1)
        vehicle_name = 'CON' if tab_active=='left' else 'CẨU'
        worksheet.merge_range('A5:K5', 'LỊCH XE '+vehicle_name+' TUẦN '+str(data['week'])+' - TỪ NGÀY '+data['start']+' ĐẾN NGÀY '+data['end'], format1)
        worksheet.merge_range('A6:I6', 'Ngày in: '+arr_date[0]+' tháng '+arr_date[1]+' năm '+arr_date[2], format_date)

        worksheet.write('A7', 'Thứ/Ngày', format_title)
        worksheet.write('B7', 'Thời gian đi/đến', format_title)
        worksheet.write('C7', 'Nơi đi', format_title)
        worksheet.write('D7', 'Nơi đến', format_title)
        worksheet.write('E7', 'Nội dung', format_title)
        worksheet.write('F7', 'Đơn vị đăng ký', format_title)
        worksheet.write('G7', 'Lái xe', format_title)
        worksheet.write('H7', 'Xe', format_title)
        if tab_active == 'left':
            worksheet.write('I7', 'Ghi chú', format_title)
        elif tab_active == 'right':
            worksheet.write('I7', 'Km vận chuyển', format_title)
            worksheet.write('J7', 'Giờ cẩu dự kiến', format_title)
            worksheet.write('K7', 'Ghi chú', format_title)

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
            if len(arr_seq) < 7:
                arr_seq.append(begin_row)

            # Iterate over the data and write it out row by row (Lịch)
            row_count = arr_seq[index]
            for item_info in data['calender']:
                if item['date'] == item_info['date']:
                    driver_list = []
                    for driv in item_info['drivers']:
                        driver_str = ""
                        driver_str = driv['dep_name'] + "-" + driv['last_name']
                        driver_list.append(driver_str)
                    drivers = ", ".join(driver_list)

                    vehicle_list = []
                    for vehi in item_info['vehicles']:
                        vehicle_str = ""
                        vehicle_str = "%s (%s)" % (vehi['name'], vehi['number'])
                        vehicle_list.append(vehicle_str)
                    vehicles = ", ".join(vehicle_list)

                    if item['date'] == item_info['end_time'].strftime("%d-%m-%Y"):
                        worksheet.write(row_count, 1, item_info['starttime']+' - '+item_info['endtime'], format2)
                    else:
                        date_str = f"Từ: {item_info['starttime']} {item_info['start_time'].strftime('%d-%m-%Y')} \n \
                                    Đến: {item_info['endtime']} {item_info['end_time'].strftime('%d-%m-%Y')}"
                        worksheet.write(row_count, 1, date_str, format2)

                    worksheet.write(row_count, 2, item_info['departure'], format_justify)
                    worksheet.write(row_count, 3, item_info['destination'], format_justify)
                    worksheet.write(row_count, 4, item_info['content'], format2)
                    worksheet.write(row_count, 5, item_info['register_unit_name'], format2)
                    worksheet.write(row_count, 6, drivers, format2)
                    worksheet.write(row_count, 7, vehicles, format2)
                    if tab_active == 'left':
                        worksheet.write(row_count, 8, item_info['note'], format2)
                    elif tab_active == 'right':
                        worksheet.write(row_count, 8, item_info['expected_km'], format2)
                        worksheet.write(row_count, 9, item_info['expected_crane_hour'], format2)
                        worksheet.write(row_count, 10, item_info['note'], format2)
                    row_count = row_count + 1
                
            if item['count'] == 0:
                worksheet.write(row_count, 1, '', format2)
                worksheet.write(row_count, 2, '', format_justify)
                worksheet.write(row_count, 3, '', format_justify)
                worksheet.write(row_count, 4, '', format2)
                worksheet.write(row_count, 5, '', format2)
                worksheet.write(row_count, 6, '', format2)
                worksheet.write(row_count, 7, '', format2)
                if tab_active == 'left':
                    worksheet.write(row_count, 8, '', format2)
                elif tab_active == 'right':
                    worksheet.write(row_count, 8, '', format2)
                    worksheet.write(row_count, 9, '', format2)
                    worksheet.write(row_count, 10, '', format2)

        begin_row_footer = begin_row + 1
        
        worksheet.merge_range(begin_row_footer, 5, begin_row_footer, 6, 'TL.GIÁM ĐỐC', format1)
        worksheet.merge_range(begin_row_footer + 1, 5, begin_row_footer + 1, 6, 'CHÁNH VĂN PHÒNG', format1)

        workbook.close()
        return response
    else:
        return redirect('/vehicle/unexpected_error/')

def excel_data(date, department_id, tab_active, status):
    try:
        date_data = start_end_of_week(date)
        week = convertNumberWeek(date)
        # status = getCalenderStatus_vt(week)
        calender = sql_calender_detail(date, department_id, True if tab_active=="left" else False, status)
        date_list = date_of_week(date, department_id, True if tab_active=="left" else False, status)
        context = {
            'date': date,
            'start': date_data['start'],
            'end': date_data['end'],
            'week': week,
            'date_list': date_list,
            'calender': calender
        }
        return context
    except Exception as exc:
        LoggingFile(exc)
        return redirect('/vehicle/unexpected_error/')
