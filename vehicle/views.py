from shutil import ExecError
from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime, timedelta
from django.views import View
from django.http import HttpResponse
from django.views.generic import DetailView
from calender.views import connect_sql, start_end_of_week, addOneDate, convertDate, week, \
    convertNumberWeek, getGroupUserId, no_accent, execute_sql, getDepartmentUserId, getlistusers, \
    reload_confirm_division, group_by_depart
from calender.models import *
from .models import VehicleCalender as ModelVehicleCalender, Vehicle, Vehicle_Division, Driver_Division, VehicleWorkingStage, AssignedUser
from .forms import CalenderUpdateDetailForm, CalenderDisableForm, CalenderAddForm, VehicleWorkingStageForm
import json, logging, xlsxwriter
from django.contrib.auth.models import User, Group
from vehicle.models import *
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from .utils import cal_fee_on_km, get_user_management_depart, convert_number, cal_liter_on_km, Calculation as Cal
from collections import Counter
from vietnam_number import n2w

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

def sql_calender_detail(date, departmt, is_left_tab, status="ALL", has_perm_driver=False, user_id=None):
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

            item_id = item['id']
            # If vehicle calender exist week calender
            if item["calender_id"]:
                item_id = item["calender_id"]
                assign_model = 'calender_working_division'
            else:
                assign_model = 'vehicle_assigneduser'

            sql_division = """select cwd.user_id, u.first_name, u.last_name, u.username, cd.name from %s as cwd inner join (select user_id, first_name, last_name, username, department_id from auth_user au inner join calender_profile cp on au.id = cp.user_id) u on u.user_id = cwd.user_id
                left join calender_department cd on cd.id = u.department_id where cwd.active = 1 and cwd.calender_id = %s"""
            rs_division = connect_sql(sql_division % (assign_model, item_id))
            item['division_list'] = acronym_depart(rs_division)
            item['filter_group'] = group_by_depart(rs_division)

            view_btn_work_perform = False
            
            has_perm_work_perform = check_perm_work_perform(user_id, item["id"])

            if has_perm_driver or has_perm_work_perform:
                view_btn_work_perform = True
            
            item['view_btn_work_perform'] = view_btn_work_perform

            # Checking if all business working stage has confirmed then change color of calendar record
            all_confirmed = False
            calender_stage = Vehicle_Division.objects.filter(calender=item['id'], active=True).count()
            confirmed_stage = VehicleWorkingStage.objects.filter(calender=item['id'], status='CONFIRM').count()

            if calender_stage == confirmed_stage and calender_stage > 0:
                all_confirmed = True
            
            item['all_confirmed'] = all_confirmed

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

            getDepart = getDepartmentUserId(user_id)
            list_users = getlistusers(getDepart[0]['department_id'])

            has_perm_driver = request.user.has_perm("vehicle.driver_vehicle")

            week = convertNumberWeek(date_left)
            week_right = convertNumberWeek(date_right)
            status_list = ModelVehicleCalender.STATUS
            register_unit_list = Department.objects.filter(active=True, is_vehicle_calender=True).order_by('group', 'sequence')
            calender_list = sql_calender_detail(date_left, depa_left, True, stat_left, has_perm_driver, user_id)
            date_list = date_of_week(date_left, depa_left, True, stat_left)
            # =================TAB TO THE RIGHT=================
            calender_list_right = sql_calender_detail(date_right, depa_right, False, stat_right, has_perm_driver, user_id)
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
                'has_perm_assign': has_perm_assign,
                'list_users': list_users
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
        status_before_edit = calender.status
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
            if form.is_valid() and form.has_changed():
                #  and form.has_changed()
                post = form.save(commit=False)
                post.week = int(form.cleaned_data['start_time'].strftime("%V")) + 1
                post.write_uid = request.user
                post.write_date = datetime.now()
                post.save()
                # print("form error :", form.errors.as_data())

                driver_list = Driver_Division.objects.filter(calender=cid)
                if post.status == 'CANCEL' and len(driver_list) > 0 and status_before_edit != post.status:
                    for driver in driver_list:
                        insert_chat = "INSERT INTO QNaPC_ChangeToChat_PhuongTien(id, id_pb, username, sended, send_time, cancel_status, write_date, user_edit)  VALUES (%s, NULL, NULL, 0, NULL, %s, %s, %s)"
                        execute_sql(insert_chat, cid, 1, datetime.now(), driver.driver.id) # assign id_status=1 temporary
                    assign_perm_users = User.objects.filter(user_permissions__codename='assign_vehicle')
                    # print(assign_perm_users)
                    # Just apply for user, not group has permission
                    for user in assign_perm_users:
                        insert_chat = "INSERT INTO QNaPC_ChangeToChat_PhuongTien(id, id_pb, username, sended, send_time, cancel_status, write_date, user_edit)  VALUES (%s, NULL, NULL, 0, NULL, %s, %s, %s)"
                        execute_sql(insert_chat, cid, 1, datetime.now(), user.id) # assign id_status=1 temporary
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
                post.week = int(form.cleaned_data['start_time'].strftime("%V")) + 1
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
                # Apply for when select approval user
                if post.approved_by:
                    insert_chat = "INSERT INTO QNaPC_ChangeToChat_PhuongTien(id, id_pb, username, sended, send_time, cancel_status, write_date, user_edit)  VALUES (%s, NULL, NULL, 0, NULL, %s, %s, %s)"
                    execute_sql(insert_chat, post.id, 1, datetime.now(), post.approved_by.id) # assign id_status=1 temporary
                return redirect('/admin/vehicle/vehiclecalender/')
            # print("form error :", form.errors.as_data())
        else:
            user_depart = get_user_management_depart(request.user.id)
            form = CalenderAddForm(initial={ 'vehicle_type': 1, 'management_fee': user_depart })

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
                
                if calendar.is_appr_manager and user_id == calendar.approved_by.id:
                    assign_perm_users = User.objects.filter(user_permissions__codename='assign_vehicle')
                    # Just apply for user, not group has permission
                    for user in assign_perm_users:
                        insert_chat = "INSERT INTO QNaPC_ChangeToChat_PhuongTien(id, id_pb, username, sended, send_time, cancel_status, write_date, user_edit)  VALUES (%s, NULL, NULL, 0, NULL, %s, %s, %s)"
                        execute_sql(insert_chat, cal, 1, datetime.now(), user.id) # assign id_status=1 temporary
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

def view_form(request):
    try:
        current_date = datetime.now().strftime('%d-%m-%Y')
        vehicle_list = Vehicle.objects.all()

        context = {
            'show_button_export': False,
            'date_from': current_date,
            'date_to': current_date,
            'vehicle_id': 0,
            'vehicle_list': vehicle_list,
            'data_list': [],
            'url_name': '',
            'form_id': '0'
        }
        return render(request, "vehicle/form_view.html", context)
    except Exception as exc:
        print(exc)
        LoggingFile(exc)
        return redirect('/vehicle/unexpected_error/')

def get_form_id(id):
    form_dict = {
        '1': 'export_xlsx_routine',
        '2': 'export_xlsx_form_1',
        '3': 'export_xlsx_form_2',
        '4': 'export_xlsx_form_3',
        '5': 'export_xlsx_form_4',
        '6': 'export_xlsx_form_5'
    }
    url_name = form_dict[id]
    return url_name

def get_form(request):
    try:
        date_from = request.GET['date_from']
        date_to = request.GET['date_to']
        form_id = request.GET['form_id']
        vehicle_id = request.GET['vehicle_id']

        if date_from and date_to:
            _date_from = convertDate(date_from) + ' 00:00:00'
            _date_to = convertDate(date_to) + ' 23:59:59'
        
            data_list = get_stage_info(_date_from, _date_to, vehicle_id)

            # Show button export excel
            show_button_export = False
            if len(data_list) > 0:
                show_button_export = True

            # Get url name to active event click
            url_name = get_form_id(form_id)

            vehicle_list = Vehicle.objects.all()

            context = {
                'show_button_export': show_button_export,
                'date_from': date_from,
                'date_to': date_to,
                'vehicle_id': int(vehicle_id),
                'vehicle_list': vehicle_list,
                'data_list': data_list,
                'url_name': url_name,
                'form_id': form_id
            }
            return render(request, "vehicle/form_view.html", context)
    except Exception as exc:
        print(exc)
        LoggingFile(exc)
        return redirect('/vehicle/unexpected_error/')

def get_stage_info(date_from, date_to, vehicle_id, fuel_type='petrol'):
    try:
        sql = """
                SELECT v.id, v.number, vc.content, FORMAT(vws.start_km, 'N', 'vi-VN') AS start_km, FORMAT(vws.end_km, 'N', 'vi-VN') AS end_km, 
            CONVERT(VARCHAR(10), vws.create_date, 105) as create_date, coalesce(vws.crane_hour, '') AS crane_hour, coalesce(vws.generator_firing_hour, '') AS generator_firing_hour, vc.management_fee
            FROM vehicle_vehicleworkingstage AS vws INNER JOIN vehicle_vehiclecalender AS vc ON vws.calender_id = vc.id
            INNER JOIN vehicle_vehicle as v ON v.id = vws.vehicle_id 
            WHERE vws.create_date  BETWEEN '%s' AND '%s'""" % (date_from, date_to)

        if vehicle_id != '0':
            sql += ' AND v.id = %s' % (vehicle_id,)
        
        if fuel_type == 'diesel':
            sql += ' AND v.vehicle_type_id != 1'
        
        data = connect_sql(sql)
        
        return data

    except Exception as exc:
        print(exc)
        LoggingFile(exc)
        return []

def get_fuel_settlement(date_from, date_to, vehicle_id):
    try:
        sql = """
            WITH fee_management AS (SELECT v.id, v.number, SUM(vws.start_km) AS start_km, SUM(vws.end_km) AS end_km, vc.management_fee, vft.name AS fuel_type
                    FROM vehicle_vehicleworkingstage AS vws INNER JOIN vehicle_vehiclecalender AS vc ON vws.calender_id = vc.id
                    INNER JOIN vehicle_vehicle as v ON v.id = vws.vehicle_id
                    LEFT JOIN vehicle_fueltype as vft ON v.fuel_type_id = vft.id
                WHERE vws.create_date  BETWEEN '%s' AND '%s' AND v.vehicle_type_id = 1
            GROUP BY v.id, v.number, vc.management_fee, vft.name
            HAVING vc.management_fee = 1
        ), nfm AS 
        (SELECT v.id, v.number, SUM(vws.start_km) AS start_km, SUM(vws.end_km) AS end_km, vc.management_fee, vft.name AS fuel_type
                    FROM vehicle_vehicleworkingstage AS vws INNER JOIN vehicle_vehiclecalender AS vc ON vws.calender_id = vc.id
                    INNER JOIN vehicle_vehicle as v ON v.id = vws.vehicle_id
                    LEFT JOIN vehicle_fueltype as vft ON v.fuel_type_id = vft.id
                WHERE vws.create_date  BETWEEN '%s' AND '%s' AND v.vehicle_type_id = 1
            GROUP BY v.id, v.number, vc.management_fee, vft.name
            HAVING vc.management_fee = 0
        )
        SELECT fee_management.number, fee_management.id, FORMAT(fee_management.start_km, 'N', 'vi-VN') AS start_km, FORMAT(fee_management.end_km, 'N', 'vi-VN') AS end_km, fee_management.management_fee, fee_management.fuel_type, FORMAT(nfm.start_km, 'N', 'vi-VN') AS nfm_start_km, 
        FORMAT(nfm.end_km, 'N', 'vi-VN') AS nfm_end_km, nfm.management_fee AS nfm_management_fee, nfm.fuel_type AS nfm_fuel_type FROM fee_management
        LEFT JOIN nfm ON fee_management.id = nfm.id 
            """ % (date_from, date_to, date_from, date_to)
        if vehicle_id != '0':
            sql += ' AND v.id = %s' % (vehicle_id,)
        
        data = connect_sql(sql)
        
        return data

    except Exception as exc:
        print(exc)
        LoggingFile(exc)
        return []

# BM3
def get_crane_fuel_settlement(date_from, date_to, vehicle_id):
    try:
        sql = """
            WITH total AS (SELECT v.id, v.number, SUM(vws.start_km) AS start_km, SUM(vws.end_km) AS end_km, SUM(vws.crane_hour) AS crane_hour, SUM(vws.generator_firing_hour) AS generator_firing_hour
                    FROM vehicle_vehicleworkingstage AS vws INNER JOIN vehicle_vehiclecalender AS vc ON vws.calender_id = vc.id
                    INNER JOIN vehicle_vehicle as v ON v.id = vws.vehicle_id
                WHERE v.vehicle_type_id != 1 
                    AND vws.create_date  BETWEEN '{from}' AND '{to}'
            GROUP BY v.id, v.number
        ), total_sxkd AS 
        (SELECT v.id, v.number, SUM(vws.start_km) AS start_km, SUM(vws.end_km) AS end_km, SUM(vws.crane_hour) AS crane_hour, SUM(vws.generator_firing_hour) AS generator_firing_hour
                    FROM vehicle_vehicleworkingstage AS vws INNER JOIN vehicle_vehiclecalender AS vc ON vws.calender_id = vc.id
                    INNER JOIN vehicle_vehicle as v ON v.id = vws.vehicle_id 
                WHERE v.vehicle_type_id != 1
                    AND vws.create_date  BETWEEN '{from}' AND '{to}'
            GROUP BY v.id, v.number, vc.management_fee
            HAVING vc.management_fee = 0
        ), total_dtxd AS 
        (SELECT v.id, v.number, SUM(vws.start_km) AS start_km, SUM(vws.end_km) AS end_km, SUM(vws.crane_hour) AS crane_hour, SUM(vws.generator_firing_hour) AS generator_firing_hour
                    FROM vehicle_vehicleworkingstage AS vws INNER JOIN vehicle_vehiclecalender AS vc ON vws.calender_id = vc.id
                    INNER JOIN vehicle_vehicle as v ON v.id = vws.vehicle_id 
                WHERE v.vehicle_type_id != 1  
                    AND vws.create_date  BETWEEN '{from}' AND '{to}'
            GROUP BY v.id, v.number, vc.management_fee
            HAVING vc.management_fee = 1
        )
        SELECT total.number, total.id, total.start_km, total.end_km, total.crane_hour, total.generator_firing_hour, 
        total_sxkd.start_km AS sxkd_start_km, total_sxkd.end_km AS sxkd_end_km, total_sxkd.crane_hour AS sxkd_crane_hour, total_sxkd.generator_firing_hour AS sxkd_generator_firing_hour,
        total_dtxd.start_km AS dtxd_start_km, total_dtxd.end_km AS dtxd_end_km, total_dtxd.crane_hour AS dtxd_crane_hour, total_dtxd.generator_firing_hour AS dtxd_generator_firing_hour
        FROM total
        LEFT JOIN total_sxkd ON total.id = total_sxkd.id 
        LEFT JOIN total_dtxd ON total.id = total_dtxd.id 
            """.format(**{"from": date_from , "to": date_to})
        
        if vehicle_id != '0':
            sql += ' AND v.id = %s' % (vehicle_id,)
        
        data = connect_sql(sql)
        
        return data

    except Exception as exc:
        print(exc)
        LoggingFile(exc)
        return []

def get_bqlda_fuel_settlement(date_from, date_to, vehicle_id):
    try:
        sql = """
            SELECT v.id, v.number, vc.content, FORMAT(vws.start_km, 'N', 'vi-VN') AS start_km, FORMAT(vws.end_km, 'N', 'vi-VN') AS end_km, 
                vc.destination, vc.content, vft.price, vc.note,
                CONVERT(VARCHAR(10), vws.create_date, 105) as create_date, coalesce(vws.crane_hour, '') AS crane_hour, coalesce(vws.generator_firing_hour, '') AS generator_firing_hour, vc.management_fee
                FROM vehicle_vehicleworkingstage AS vws INNER JOIN vehicle_vehiclecalender AS vc ON vws.calender_id = vc.id
                INNER JOIN vehicle_vehicle as v ON v.id = vws.vehicle_id 
                LEFT JOIN vehicle_fueltype as vft ON v.fuel_type_id = vft.id
                WHERE vc.management_fee = 1
                AND vws.create_date  BETWEEN '{from}' AND '{to}'
            """.format(**{"from": date_from , "to": date_to})
        
        if vehicle_id != '0':
            sql += ' AND v.id = %s' % (vehicle_id,)
        
        data = connect_sql(sql)
        
        return data

    except Exception as exc:
        print(exc)
        LoggingFile(exc)
        return []

def export_xlsx_routine(request):
    if request.method == "GET" and request.user.pk:

        date_from = request.GET['date_from']
        date_to = request.GET['date_to']
        vehicle_id = request.GET['vehicle_id']

        data_list = []
        if date_from and date_to:
            _date_from = convertDate(date_from) + ' 00:00:00'
            _date_to = convertDate(date_to) + ' 23:59:59'
            data_list = get_stage_info(_date_from, _date_to, vehicle_id)
        
        # If vehicle option is 'ALL' then adding 1 column 'VEHICLE'
        vehicle_name = ''
        column_start = 0
        if vehicle_id == '0':
            vehicle_name = 'TẤT CẢ XE'
            column_start = 1
        else:
            vehicle = Vehicle.objects.get(id=int(vehicle_id))
            if vehicle:
                vehicle_name = '%s (%s)' % (vehicle.name, vehicle.number)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = "attachment; filename=BieuMauNhatTrinh.xlsx"
        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    
        worksheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True, 'text_wrap': 1})
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_font('Times New Roman')

        worksheet.print_area('A1:H20')
        worksheet.fit_to_pages(1, 0)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)

        worksheet.set_default_row(30)

        # Set width column
        worksheet.set_column('A:A', 13)

        title_range = 'A1:H1'
        b_column = 50
        if column_start:
            title_range = 'A1:I1'
            b_column = 13
            worksheet.set_column('C:C', 50)
            worksheet.set_column('D:I', 13)
        else:
            worksheet.set_column('C:H', 13)

        worksheet.set_column('B:B', b_column)

        worksheet.merge_range(title_range, 'NHẬT TRÌNH CỦA XE BIỂN KIỂM SOÁT: %s \n Từ ngày %s đến ngày %s' % (vehicle_name, date_from, date_to), format1)
        worksheet.merge_range(1, 0, 2, 0, 'Ngày tháng', format1)
        
        if column_start:
            worksheet.merge_range(1, column_start, 2, column_start, 'Xe', format1)

        worksheet.merge_range(1, column_start + 1, 2, column_start + 1, 'Nội dung và khối lượng công việc thực hiện', format1)
        
        worksheet.merge_range(1, column_start + 2, 1, column_start + 4, 'Số Km vận hành', format1)
        worksheet.write(2, column_start + 2, 'Đầu kỳ', format1)
        worksheet.write(2, column_start + 3, 'Cuối kỳ', format1)
        worksheet.write(2, column_start + 4, 'Phát sinh', format1)

        worksheet.merge_range(1, column_start + 5, 2, column_start + 5, 'Giờ cẩu', format1)
        worksheet.merge_range(1, column_start + 6, 2, column_start + 6, 'Giờ chạy máy phát (Xe Hotline)', format1)
        worksheet.merge_range(1, column_start + 7, 2, column_start + 7, 'Ký xác nhận (ghi rõ họ tên)', format1)

        begin_row = 3
        for line in data_list:
            worksheet.write(begin_row, 0, line['create_date'], format1)
            if column_start:
                worksheet.write(begin_row, column_start, line['number'], format1)
            worksheet.write(begin_row, column_start + 1, line['content'], format1)
            worksheet.write(begin_row, column_start + 2, line['start_km'].replace(',00', '') if ',00' in line['start_km'] else '', format1)
            worksheet.write(begin_row, column_start + 3, line['end_km'].replace(',00', '') if ',00' in line['end_km'] else '', format1)

            km_total = 0
            if line['start_km'] and line['end_km']:

                start_km = convert_number(line['start_km'])
                end_km = convert_number(line['end_km'])

                if start_km < end_km:
                    km_total = end_km - start_km

            worksheet.write(begin_row, column_start + 4, Cal.convert_dot(km_total), format1)
            worksheet.write(begin_row, column_start + 5, line['crane_hour'], format1)
            worksheet.write(begin_row, column_start + 6, line['generator_firing_hour'], format1)

            begin_row += 1

        workbook.close()
        return response

    else:
        return redirect('/vehicle/unexpected_error/')

def export_xlsx_form_1(request):
    if request.method == "GET" and request.user.pk:
        date_from = request.GET['date_from']
        date_to = request.GET['date_to']
        vehicle_id = request.GET['vehicle_id']

        data_list = []
        if date_from and date_to:
            _date_from = convertDate(date_from) + ' 00:00:00'
            _date_to = convertDate(date_to) + ' 23:59:59'
            data_list = get_stage_info(_date_from, _date_to, vehicle_id)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = "attachment; filename=BienBanKiemTraChiSoKm.xlsx"
        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    
        worksheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1})
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_font('Times New Roman')

        format_border = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1, 'border': 1})
        format_border.set_align('center')
        format_border.set_align('vcenter')
        format_border.set_font('Times New Roman')

        format_fs10 = workbook.add_format({'font_size': 11, 'align': 'center', 'text_wrap': 1})
        format_fs10.set_align('center')
        format_fs10.set_align('vcenter')
        format_fs10.set_font('Times New Roman')

        format_unl = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1})
        format_unl.set_align('center')
        format_unl.set_align('vcenter')
        format_unl.set_font('Times New Roman')
        format_unl.set_underline()

        format_itl = workbook.add_format({'font_size': 12, 'align': 'center', 'text_wrap': 1})
        format_itl.set_align('center')
        format_itl.set_align('vcenter')
        format_itl.set_font('Times New Roman')
        format_itl.set_italic()

        format_left_align = workbook.add_format({'font_size': 12, 'align': 'left', 'text_wrap': 1})
        format_left_align.set_font('Times New Roman')

        worksheet.print_area('A1:H40')
        worksheet.fit_to_pages(1, 0)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)

        worksheet.set_default_row(20)

        # Set width column
        worksheet.set_column('A:A', 5)

        worksheet.set_column('B:P', 10)
        
        worksheet.merge_range('A1:C1', 'CÔNG TY ĐIỆN LỰC QUẢNG NAM', format_fs10)
        worksheet.merge_range('D1:H1', 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', format1)

        worksheet.merge_range('A2:C2', 'VĂN PHÒNG', format_unl)
        worksheet.merge_range('D2:H2', 'Độc lập - Tự do - Hạnh Phúc', format_unl)

        worksheet.merge_range('D4:H4', datetime.now().strftime('Tam Kỳ, ngày %d tháng %m năm %Y'), format_itl)

        worksheet.merge_range('A5:H5', 'BIÊN BẢN KIỂM TRA CHỐT CHỈ SỐ KM', format1)
        worksheet.merge_range('A6:H6', 'Hôm nay, vào lúc ... giờ 00 phút ngày ... tháng ... năm 2022 chúng tôi gồm có :', format_left_align)
        worksheet.merge_range('A7:C7', 'Ông:', format_left_align)
        worksheet.merge_range('D7:H7', 'Chức vụ: Phó Chánh Văn Phòng', format_left_align)
        worksheet.merge_range('A8:C8', 'Ông:', format_left_align)
        worksheet.merge_range('D8:H8', 'Chức vụ: Lái xe', format_left_align)

        worksheet.merge_range('A9:H9', 'Cùng kiểm tra chốt chỉ số km các phương tiện vận tải, cụ thể sau:', format_left_align)

        worksheet.merge_range(10, 0, 11, 0, 'STT', format_border)
        worksheet.merge_range(10, 1, 11, 1, 'Tên PTVT', format_border)
        worksheet.merge_range(10, 2, 11, 2, 'Km đầu kỳ', format_border)
        worksheet.merge_range(10, 3, 11, 3, 'Km cuối kỳ', format_border)
        worksheet.merge_range(10, 4, 10, 6, 'Km phát sinh', format_border)

        worksheet.write('E12', 'Tổng Km', format_border)
        worksheet.write('F12', 'Phục vụ SXKD', format_border)
        worksheet.write('G12', ' Ban QLDA', format_border)

        worksheet.merge_range(10, 7, 11, 7, 'Ghi chú', format_border)

        begin_row = 12
        stt = 1
        km_amount = 0
        sxkd_amount = 0
        qlda_amount = 0

        for line in data_list:
            worksheet.write(begin_row, 0, stt, format_border)
            worksheet.write(begin_row, 1, line['number'], format_border)
            # worksheet.write(begin_row, 0, line['create_date'], format1)
            # worksheet.write(begin_row, 2, line['content'], format1)
            worksheet.write(begin_row, 2, line['start_km'].replace(',00', '') if line['start_km'] else '', format_border)
            worksheet.write(begin_row, 3, line['end_km'].replace(',00', '') if line['end_km'] else '', format_border)

            km_total = 0
            if line['start_km'] and line['end_km']:
                start_km = float(line['start_km'].replace(',00', '').replace('.', ''))
                end_km = float(line['end_km'].replace(',00', '').replace('.', ''))
                if start_km < end_km:
                    km_total = end_km - start_km

            worksheet.write(begin_row, 4, Cal.convert_dot(km_total), format_border)

            amount_total = cal_fee_on_km(km_total, line['id'])

            sxkd_total = 0
            qlda_total = 0
            if not line['management_fee']:
                sxkd_total = amount_total
                worksheet.write(begin_row, 5, Cal.convert_dot(sxkd_total), format_border)
                worksheet.write(begin_row, 6, 0, format_border)
            else:
                qlda_total = amount_total
                worksheet.write(begin_row, 5, 0, format_border)
                worksheet.write(begin_row, 6, Cal.convert_dot(qlda_total), format_border)
            worksheet.write(begin_row, 7, '', format_border)
            
            stt += 1
            begin_row += 1

            km_amount += km_total
            sxkd_amount += sxkd_total
            qlda_amount += qlda_total
        
        worksheet.merge_range(begin_row, 0, begin_row, 2, 'Tổng cộng: ', format_border)
        worksheet.write(begin_row, 3, '', format_border)
        worksheet.write(begin_row, 4, Cal.convert_dot(km_amount), format_border)
        worksheet.write(begin_row, 5, Cal.convert_dot(sxkd_amount), format_border)
        worksheet.write(begin_row, 6, Cal.convert_dot(qlda_amount), format_border)
        worksheet.write(begin_row, 7, '', format_border)

        worksheet.merge_range(begin_row + 1, 0, begin_row + 1, 4, 'Biên bản kết thúc vào lúc ... giờ ... phút cùng ngày.', format_left_align)

        worksheet.merge_range(begin_row + 3, 0, begin_row + 3, 7, 'HỘI ĐỒNG KIỂM TRA', format1)
        worksheet.merge_range(begin_row + 4, 0, begin_row + 4, 3, 'VĂN PHÒNG', format1)
        worksheet.merge_range(begin_row + 4, 4, begin_row + 4, 7, 'NGƯỜI LẬP', format1)

        workbook.close()
        return response

    else:
        return redirect('/vehicle/unexpected_error/')

def export_xlsx_form_2(request):
    if request.method == "GET" and request.user.pk:
        date_from = request.GET['date_from']
        date_to = request.GET['date_to']
        vehicle_id = request.GET['vehicle_id']

        data_list = []
        if date_from and date_to:
            _date_from = convertDate(date_from) + ' 00:00:00'
            _date_to = convertDate(date_to) + ' 23:59:59'
            data_list = get_stage_info(_date_from, _date_to, vehicle_id, 'diesel')

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = "attachment; filename=BienBanKiemTraChiSoKmXeCau.xlsx"
        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    
        worksheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1})
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_font('Times New Roman')

        format_border = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1, 'border': 1})
        format_border.set_align('center')
        format_border.set_align('vcenter')
        format_border.set_font('Times New Roman')

        format_fs10 = workbook.add_format({'font_size': 11, 'align': 'center', 'text_wrap': 1})
        format_fs10.set_align('center')
        format_fs10.set_align('vcenter')
        format_fs10.set_font('Times New Roman')

        format_unl = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1})
        format_unl.set_align('center')
        format_unl.set_align('vcenter')
        format_unl.set_font('Times New Roman')
        format_unl.set_underline()

        format_itl = workbook.add_format({'font_size': 12, 'align': 'center', 'text_wrap': 1})
        format_itl.set_align('center')
        format_itl.set_align('vcenter')
        format_itl.set_font('Times New Roman')
        format_itl.set_italic()

        format_left_align = workbook.add_format({'font_size': 12, 'align': 'left', 'text_wrap': 1})
        format_left_align.set_font('Times New Roman')

        worksheet.print_area('A1:H40')
        worksheet.fit_to_pages(1, 0)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)

        worksheet.set_default_row(20)

        # Set width column
        worksheet.set_column('A:A', 5)

        worksheet.set_column('B:P', 10)
        
        worksheet.merge_range('A1:C1', 'CÔNG TY ĐIỆN LỰC QUẢNG NAM', format_fs10)
        worksheet.merge_range('D1:H1', 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', format1)

        worksheet.merge_range('A2:C2', 'VĂN PHÒNG', format_unl)
        worksheet.merge_range('D2:H2', 'Độc lập - Tự do - Hạnh Phúc', format_unl)

        worksheet.merge_range('D4:H4', datetime.now().strftime('Quảng Nam, ngày %d tháng %m năm %Y'), format_itl)

        worksheet.merge_range('A5:H5', 'BIÊN BẢN KIỂM TRA CHỐT CHỈ SỐ KM XE CẨU', format1)
        worksheet.merge_range('A6:H6', 'Hôm nay, vào lúc ... giờ 00 phút ngày ... tháng ... năm 2022 chúng tôi gồm có :', format_left_align)
        worksheet.merge_range('A7:C7', 'Ông:', format_left_align)
        worksheet.merge_range('D7:H7', 'Chức vụ: Phó Chánh Văn Phòng', format_left_align)
        worksheet.merge_range('A8:C8', 'Ông:', format_left_align)
        worksheet.merge_range('D8:H8', 'Chức vụ: Lái xe', format_left_align)

        worksheet.merge_range('A9:H9', 'Cùng kiểm tra chốt chỉ số km các phương tiện vận tải, cụ thể sau:', format_left_align)

        worksheet.merge_range(10, 0, 11, 0, 'STT', format_border)
        worksheet.merge_range(10, 1, 11, 1, 'Tên PTVT', format_border)
        worksheet.merge_range(10, 2, 11, 2, 'Km đầu kỳ', format_border)
        worksheet.merge_range(10, 3, 11, 3, 'Km cuối kỳ', format_border)
        worksheet.merge_range(10, 4, 11, 4, 'Km phát sinh', format_border)
        worksheet.merge_range(10, 5, 11, 5, 'Giờ cẩu', format_border)
        worksheet.merge_range(10, 6, 11, 6, 'Ghi chú', format_border)

        begin_row = 12
        stt = 1

        km_amount = 0
        crane_amount = 0
        for line in data_list:
            worksheet.write(begin_row, 0, stt, format_border)
            worksheet.write(begin_row, 1, line['number'], format_border)
            worksheet.write(begin_row, 2, line['start_km'].replace(',00', '') if line['start_km'] else '', format_border)
            worksheet.write(begin_row, 3, line['end_km'].replace(',00', '') if line['end_km'] else '', format_border)

            km_total = 0
            if line['start_km'] and line['end_km']:
                start_km = float(line['start_km'].replace(',00', '').replace('.', ''))
                end_km = float(line['end_km'].replace(',00', '').replace('.', ''))
                if start_km < end_km:
                    km_total = end_km - start_km

            worksheet.write(begin_row, 4, Cal.convert_dot(km_total), format_border)

            worksheet.write(begin_row, 5, line['crane_hour'], format_border)
            worksheet.write(begin_row, 6, '', format_border)

            km_amount += km_total
            crane_amount += line['crane_hour']
            
            stt += 1
            begin_row += 1
        
        worksheet.write(begin_row, 0, '', format_border)
        worksheet.merge_range(begin_row, 1, begin_row, 2, 'Tổng cộng: ', format_border)
        worksheet.write(begin_row, 3, '', format_border)
        worksheet.write(begin_row, 4, km_amount, format_border)
        worksheet.write(begin_row, 5, crane_amount, format_border)
        worksheet.write(begin_row, 6, '', format_border)

        worksheet.merge_range(begin_row + 1, 0, begin_row + 1, 4, 'Biên bản kết thúc vào lúc ... giờ ... phút cùng ngày.', format_left_align)

        worksheet.merge_range(begin_row + 3, 0, begin_row + 3, 7, 'HỘI ĐỒNG KIỂM TRA', format1)
        worksheet.merge_range(begin_row + 4, 0, begin_row + 4, 3, 'VĂN PHÒNG', format1)
        worksheet.merge_range(begin_row + 4, 4, begin_row + 4, 7, 'NGƯỜI LẬP', format1)

        workbook.close()
        return response

    else:
        return redirect('/vehicle/unexpected_error/')

def export_xlsx_form_3(request):
    if request.method == "GET" and request.user.pk:
        date_from = request.GET['date_from']
        date_to = request.GET['date_to']
        vehicle_id = request.GET['vehicle_id']

        data_list = []
        dmy_from = dmy_to = ''
        if date_from and date_to:
            dmy_from = (datetime.strptime(date_from, '%d-%m-%Y')).strftime('%d/%m/%Y')
            dmy_to = (datetime.strptime(date_to, '%d-%m-%Y')).strftime('%d/%m/%Y')
            _date_from = convertDate(date_from) + ' 00:00:00'
            _date_to = convertDate(date_to) + ' 23:59:59'
            data_list = get_fuel_settlement(_date_from, _date_to, vehicle_id)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = "attachment; filename=BangQuyetToanNhienLieu.xlsx"
        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    
        worksheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1})
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_font('Times New Roman')

        format_border = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1, 'border': 1})
        format_border.set_align('center')
        format_border.set_align('vcenter')
        format_border.set_font('Times New Roman')

        format_fs10 = workbook.add_format({'font_size': 11, 'align': 'center', 'text_wrap': 1})
        format_fs10.set_align('center')
        format_fs10.set_align('vcenter')
        format_fs10.set_font('Times New Roman')

        format_unl = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1})
        format_unl.set_align('center')
        format_unl.set_align('vcenter')
        format_unl.set_font('Times New Roman')
        format_unl.set_underline()

        format_itl = workbook.add_format({'font_size': 12, 'align': 'center', 'text_wrap': 1})
        format_itl.set_align('center')
        format_itl.set_align('vcenter')
        format_itl.set_font('Times New Roman')
        format_itl.set_italic()

        format_left_align = workbook.add_format({'font_size': 12, 'align': 'left', 'text_wrap': 1})
        format_left_align.set_font('Times New Roman')

        worksheet.print_area('A1:H40')
        worksheet.fit_to_pages(1, 0)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)

        worksheet.set_default_row(20)

        # Set width column
        worksheet.set_column('A:A', 5)

        worksheet.set_column('B:P', 10)
        
        worksheet.merge_range('A1:C1', 'CÔNG TY ĐIỆN LỰC QUẢNG NAM', format_fs10)
        worksheet.merge_range('D1:L1', 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', format1)

        worksheet.merge_range('A2:C2', 'VĂN PHÒNG', format_unl)
        worksheet.merge_range('D2:L2', 'Độc lập - Tự do - Hạnh Phúc', format_unl)

        worksheet.merge_range('D4:L4', datetime.now().strftime('Tam Kỳ, ngày %d tháng %m năm %Y'), format_itl)

        worksheet.merge_range('A5:L5', 'BẢNG QUYẾT TOÁN NHIÊN LIỆU', format1)
        worksheet.merge_range('A6:L6', 'Thời gian, từ ngày %s đến ngày %s' % (dmy_from, dmy_to), format_left_align)

        worksheet.merge_range(6, 0, 7, 0, 'STT', format_border)
        worksheet.merge_range(6, 1, 7, 1, 'Biển số xe', format_border)
        worksheet.merge_range(6, 2, 7, 2, 'Nội dung', format_border)
        worksheet.merge_range(6, 3, 7, 3, 'Tổng Km VH', format_border)
        worksheet.merge_range(6, 4, 7, 4, 'Tổng Xăng 95', format_border)
        worksheet.merge_range(6, 5, 7, 5, 'Tổng dầu Diezel', format_border)
        worksheet.merge_range(6, 6, 6, 8, 'NL SXKD (lít)', format_border)

        worksheet.write('G8', 'KmVH', format_border)
        worksheet.write('H8', 'Xăng', format_border)
        worksheet.write('I8', 'Diezel', format_border)

        worksheet.merge_range(6, 9, 6, 11, 'Nhiên liệu BQL', format_border)

        worksheet.write('J8', 'KmVH', format_border)
        worksheet.write('K8', 'Xăng 95', format_border)
        worksheet.write('L8', 'Dầu', format_border)

        begin_row = 8
        stt = 1
        table_total_km = table_total_petrol = table_total_diezel = 0.0
        table_nfm_total_km = table_nfm_total_petrol = table_nfm_total_diezel = 0.0
        table_fm_total_km = table_fm_total_petrol = table_fm_total_diezel = 0.0

        for line in data_list:
            worksheet.write(begin_row, 0, stt, format_border)
            worksheet.write(begin_row, 1, line['number'], format_border)
            
            worksheet.write(begin_row, 2, 'Phục vụ công tác SXKD', format_border)
            
            nfm_km_total = 0
            if line['nfm_start_km'] and line['nfm_end_km']:
                nfm_start_km = convert_number(line['nfm_start_km'])
                nfm_end_km = convert_number(line['nfm_end_km'])
                if nfm_start_km < nfm_end_km:
                    nfm_km_total = nfm_end_km - nfm_start_km

            worksheet.write(begin_row, 6, Cal.convert_dot(nfm_km_total), format_border)

            nfm_liter_total = cal_liter_on_km(nfm_km_total, line['id'])

            nfm_petrol_liter = 0.0
            nfm_diezel_liter = 0.0
            if line['nfm_fuel_type'] == 'Xăng':
                nfm_petrol_liter = nfm_liter_total
                worksheet.write(begin_row, 7, nfm_liter_total, format_border)
                worksheet.write(begin_row, 8, 0, format_border)
            else:
                nfm_diezel_liter = nfm_liter_total
                worksheet.write(begin_row, 7, 0, format_border)
                worksheet.write(begin_row, 8, nfm_liter_total, format_border)

            km_total = 0
            if line['start_km'] and line['end_km']:
                start_km = convert_number(line['start_km'])
                end_km = convert_number(line['end_km'])
                if start_km < end_km:
                    km_total = end_km - start_km

            worksheet.write(begin_row, 9, Cal.convert_dot(km_total), format_border)

            liter_total = cal_liter_on_km(km_total, line['id'])

            petrol_liter = 0.0
            diezel_liter = 0.0
            if line['fuel_type'] == 'Xăng':
                petrol_liter = liter_total
                worksheet.write(begin_row, 10, liter_total, format_border)
                worksheet.write(begin_row, 11, 0, format_border)
            else:
                diezel_liter = liter_total
                worksheet.write(begin_row, 10, 0, format_border)
                worksheet.write(begin_row, 11, liter_total, format_border)

            km_amount = nfm_km_total + km_total
            petrol_amount = nfm_petrol_liter + petrol_liter
            diezel_amount = nfm_diezel_liter + diezel_liter

            worksheet.write(begin_row, 3, Cal.convert_dot(km_amount), format_border)
            worksheet.write(begin_row, 4, petrol_amount, format_border)
            worksheet.write(begin_row, 5, diezel_amount, format_border)

            table_total_km += km_amount
            table_total_petrol += petrol_amount
            table_total_diezel += diezel_amount

            table_nfm_total_km += nfm_km_total
            table_nfm_total_petrol += nfm_petrol_liter
            table_nfm_total_diezel += nfm_diezel_liter

            table_fm_total_km += km_total
            table_fm_total_petrol += petrol_liter
            table_fm_total_diezel += diezel_liter

            stt += 1
            begin_row += 1
        
        worksheet.write(begin_row, 0, '', format_border)
        worksheet.write(begin_row, 1, 'Tổng cộng: ', format_border)
        worksheet.write(begin_row, 2, '', format_border)
        worksheet.write(begin_row, 3, table_total_km, format_border)
        worksheet.write(begin_row, 4, table_total_petrol, format_border)
        worksheet.write(begin_row, 5, table_total_diezel, format_border)
        worksheet.write(begin_row, 6, table_nfm_total_km, format_border)
        worksheet.write(begin_row, 7, table_nfm_total_petrol, format_border)
        worksheet.write(begin_row, 8, table_nfm_total_diezel, format_border)
        worksheet.write(begin_row, 9, table_fm_total_km, format_border)
        worksheet.write(begin_row, 10, table_fm_total_petrol, format_border)
        worksheet.write(begin_row, 11, table_fm_total_diezel, format_border)

        worksheet.merge_range(begin_row + 2, 0, begin_row + 2, 3, 'VĂN PHÒNG', format1)
        worksheet.merge_range(begin_row + 2, 4, begin_row + 2, 7, 'NGƯỜI LẬP', format1)

        workbook.close()
        return response

    else:
        return redirect('/vehicle/unexpected_error/')

def export_xlsx_form_4(request):
    if request.method == "GET" and request.user.pk:
        date_from = request.GET['date_from']
        date_to = request.GET['date_to']
        vehicle_id = request.GET['vehicle_id']

        data_list = []
        dmy_from = dmy_to = ''
        if date_from and date_to:
            dmy_from = (datetime.strptime(date_from, '%d-%m-%Y')).strftime('%d/%m/%Y')
            dmy_to = (datetime.strptime(date_to, '%d-%m-%Y')).strftime('%d/%m/%Y')
            _date_from = convertDate(date_from) + ' 00:00:00'
            _date_to = convertDate(date_to) + ' 23:59:59'
            data_list = get_crane_fuel_settlement(_date_from, _date_to, vehicle_id)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = "attachment; filename=BangQuyetToanNhienLieuXeCau.xlsx"
        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    
        worksheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1})
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_font('Times New Roman')

        format_border = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1, 'border': 1})
        format_border.set_align('center')
        format_border.set_align('vcenter')
        format_border.set_font('Times New Roman')

        format_fs10 = workbook.add_format({'font_size': 11, 'align': 'center', 'text_wrap': 1})
        format_fs10.set_align('center')
        format_fs10.set_align('vcenter')
        format_fs10.set_font('Times New Roman')

        format_unl = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1})
        format_unl.set_align('center')
        format_unl.set_align('vcenter')
        format_unl.set_font('Times New Roman')
        format_unl.set_underline()

        format_itl = workbook.add_format({'font_size': 12, 'align': 'center', 'text_wrap': 1})
        format_itl.set_align('center')
        format_itl.set_align('vcenter')
        format_itl.set_font('Times New Roman')
        format_itl.set_italic()

        format_left_align = workbook.add_format({'font_size': 12, 'align': 'left', 'text_wrap': 1})
        format_left_align.set_font('Times New Roman')

        worksheet.print_area('A1:H40')
        worksheet.fit_to_pages(1, 0)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)

        worksheet.set_default_row(20)

        # Set width column
        worksheet.set_column('A:A', 5)

        worksheet.set_column('B:P', 10)
        
        worksheet.merge_range('A1:C1', 'CÔNG TY ĐIỆN LỰC QUẢNG NAM', format_fs10)
        worksheet.merge_range('D1:L1', 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', format1)

        worksheet.merge_range('A2:C2', 'VĂN PHÒNG', format_unl)
        worksheet.merge_range('D2:L2', 'Độc lập - Tự do - Hạnh Phúc', format_unl)

        worksheet.merge_range('D4:L4', datetime.now().strftime('Quảng Nam, ngày %d tháng %m năm %Y'), format_itl)

        worksheet.merge_range('A5:L5', 'BẢNG QUYẾT TOÁN NHIÊN LIỆU', format1)
        worksheet.merge_range('A6:L6', 'Thời gian, từ ngày %s đến ngày %s' % (dmy_from, dmy_to), format_left_align)

        worksheet.merge_range(6, 0, 7, 0, 'STT', format_border)
        worksheet.merge_range(6, 1, 7, 1, 'Biển số xe', format_border)
        worksheet.merge_range(6, 2, 7, 2, 'Nội dung', format_border)
        worksheet.merge_range(6, 3, 7, 3, 'Tổng Km VH', format_border)
        worksheet.merge_range(6, 4, 7, 4, 'Giờ cẩu', format_border)
        worksheet.merge_range(6, 5, 7, 5, 'Giờ nổ máy', format_border)
        worksheet.merge_range(6, 6, 6, 8, 'Nhiên liệu', format_border)

        worksheet.write('G8', 'Diesel(lít)', format_border)
        worksheet.write('H8', 'TT Phục vụ SXKD', format_border)
        worksheet.write('I8', 'Phục vụ ĐTXD', format_border)

        worksheet.merge_range(6, 9, 7, 9, 'Ghi chú', format_border)

        begin_row = 8
        stt = 1
        table_total_km = table_total_crane = table_total_generator_firing = 0.0
        table_total_diesel = table_total_sxkd = table_total_dtxd = 0.0

        for line in data_list:
            worksheet.write(begin_row, 0, stt, format_border)
            worksheet.write(begin_row, 1, line['number'], format_border)
            
            worksheet.write(begin_row, 2, 'Phục vụ công tác SXKD', format_border)
            
            km_total = 0
            if line['start_km'] and line['end_km']:
                start_km = convert_number(line['start_km'])
                end_km = convert_number(line['end_km'])
                if start_km < end_km:
                    km_total = end_km - start_km

            worksheet.write(begin_row, 3, km_total, format_border)
            worksheet.write(begin_row, 4, line['crane_hour'], format_border)
            worksheet.write(begin_row, 5, line['generator_firing_hour'], format_border)

            sxkd_km_total = 0
            if line['sxkd_start_km'] and line['sxkd_end_km']:
                sxkd_start_km = convert_number(line['sxkd_start_km'])
                sxkd_end_km = convert_number(line['sxkd_end_km'])
                if sxkd_start_km < sxkd_end_km:
                    sxkd_km_total = sxkd_end_km - sxkd_start_km

            sxkd_petrol_liter = cal_liter_on_km(sxkd_km_total, line['id'])
            sxkd_crane_liter = Cal.crane_liter(line['sxkd_crane_hour'], line['id'], 'crane')
            sxkd_generator_firing_liter = Cal.crane_liter(line['sxkd_generator_firing_hour'], line['id'], 'no crane')

            sxkd_liter_total = sxkd_petrol_liter + sxkd_crane_liter + sxkd_generator_firing_liter

            worksheet.write(begin_row, 7, sxkd_liter_total, format_border)

            dtxd_km_total = 0
            if line['dtxd_start_km'] and line['dtxd_end_km']:
                dtxd_start_km = convert_number(line['dtxd_start_km'])
                dtxd_end_km = convert_number(line['dtxd_end_km'])
                if dtxd_start_km < dtxd_end_km:
                    dtxd_km_total = dtxd_end_km - dtxd_start_km

            dtxd_petrol_liter = cal_liter_on_km(dtxd_km_total, line['id'])
            dtxd_crane_liter = Cal.crane_liter(line['dtxd_crane_hour'], line['id'], 'crane')
            dtxd_generator_firing_liter = Cal.crane_liter(line['dtxd_generator_firing_hour'], line['id'], 'no crane')

            dtxd_liter_total = dtxd_petrol_liter + dtxd_crane_liter + dtxd_generator_firing_liter

            worksheet.write(begin_row, 8, dtxd_liter_total, format_border)
            worksheet.write(begin_row, 9, '', format_border)

            diesel_liter_total = sxkd_liter_total + dtxd_liter_total

            worksheet.write(begin_row, 6, diesel_liter_total, format_border)

            table_total_km += km_total
            table_total_crane += line['crane_hour']
            table_total_generator_firing += table_total_generator_firing

            table_total_diesel += diesel_liter_total
            table_total_sxkd += sxkd_liter_total
            table_total_dtxd += dtxd_liter_total

            stt += 1
            begin_row += 1
        
        worksheet.merge_range(begin_row, 0, begin_row, 2, 'Tổng cộng: ', format_border)
        worksheet.write(begin_row, 3, table_total_km, format_border)
        worksheet.write(begin_row, 4, table_total_crane, format_border)
        worksheet.write(begin_row, 5, table_total_generator_firing, format_border)
        worksheet.write(begin_row, 6, table_total_diesel, format_border)
        worksheet.write(begin_row, 7, table_total_sxkd, format_border)
        worksheet.write(begin_row, 8, table_total_dtxd, format_border)
        worksheet.write(begin_row, 9, '', format_border)

        worksheet.merge_range(begin_row + 2, 0, begin_row + 2, 3, 'VĂN PHÒNG', format1)
        worksheet.merge_range(begin_row + 2, 4, begin_row + 2, 7, 'NGƯỜI LẬP', format1)

        workbook.close()
        return response

    else:
        return redirect('/vehicle/unexpected_error/')

def export_xlsx_form_5(request):
    if request.method == "GET" and request.user.pk:
        date_from = request.GET['date_from']
        date_to = request.GET['date_to']
        vehicle_id = request.GET['vehicle_id']

        data_list = []
        vehicle_list = []
        dmy_from = dmy_to = ''
        if date_from and date_to:
            dmy_from = (datetime.strptime(date_from, '%d-%m-%Y')).strftime('%d/%m/%Y')
            dmy_to = (datetime.strptime(date_to, '%d-%m-%Y')).strftime('%d/%m/%Y')
            _date_from = convertDate(date_from) + ' 00:00:00'
            _date_to = convertDate(date_to) + ' 23:59:59'
            data_list = get_bqlda_fuel_settlement(_date_from, _date_to, vehicle_id)

            # get info of 2 keys (vehicle, count) in list
            vehicle_group = [line['number'] for line in data_list if line['number']]
            vehicle_list = list(dict.fromkeys(vehicle_group))
            vehicle_dict = [{'vehicle': line} for line in vehicle_list]
            vehicle_count = Counter(vehicle_group)
            vehicle_item = [line.update({'count': vehicle_count[line['vehicle']]}) for line in vehicle_dict]

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = "attachment; filename=BangQuyetToanNhienLieuXeCau.xlsx"
        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    
        worksheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1})
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_font('Times New Roman')

        format_border = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1, 'border': 1})
        format_border.set_align('center')
        format_border.set_align('vcenter')
        format_border.set_font('Times New Roman')

        format_fs10 = workbook.add_format({'font_size': 11, 'align': 'center', 'text_wrap': 1})
        format_fs10.set_align('center')
        format_fs10.set_align('vcenter')
        format_fs10.set_font('Times New Roman')

        format_unl = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1})
        format_unl.set_align('center')
        format_unl.set_align('vcenter')
        format_unl.set_font('Times New Roman')
        format_unl.set_underline()

        format_itl = workbook.add_format({'font_size': 12, 'align': 'center', 'text_wrap': 1})
        format_itl.set_align('center')
        format_itl.set_align('vcenter')
        format_itl.set_font('Times New Roman')
        format_itl.set_italic()

        format_title = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'text_wrap': 1, 'border': 1})
        format_title.set_align('center')
        format_title.set_align('vcenter')
        format_title.set_font('Times New Roman')
        format_title.set_bg_color('#FAEBD7')

        format_left_align = workbook.add_format({'font_size': 12, 'align': 'left', 'text_wrap': 1})
        format_left_align.set_font('Times New Roman')

        worksheet.print_area('A1:H40')
        worksheet.fit_to_pages(1, 0)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)

        worksheet.set_default_row(20)

        # Set width column
        worksheet.set_column('A:A', 5)

        worksheet.set_column('B:P', 10)
        
        worksheet.merge_range('A1:C1', 'CÔNG TY ĐIỆN LỰC QUẢNG NAM', format_fs10)
        worksheet.merge_range('D1:L1', 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', format1)

        worksheet.merge_range('A2:C2', 'VĂN PHÒNG', format_unl)
        worksheet.merge_range('D2:L2', 'Độc lập - Tự do - Hạnh Phúc', format_unl)

        worksheet.merge_range('D4:L4', datetime.now().strftime('Quảng Nam, ngày %d tháng %m năm %Y'), format_itl)

        worksheet.merge_range('A5:L5', 'BẢNG QUYẾT TOÁN NHIÊN LIỆU BQLDA', format1)
        worksheet.merge_range('A6:L6', 'Thời gian, từ ngày %s đến ngày %s' % (dmy_from, dmy_to), format_left_align)

        worksheet.write(6, 0, 'STT', format_border)
        worksheet.write(6, 1, 'Biển số xe', format_border)
        worksheet.write(6, 2, 'Địa điểm', format_border)
        worksheet.write(6, 3, 'Nội dung công việc', format_border)
        worksheet.write(6, 4, 'Km VH', format_border)
        worksheet.write(6, 5, 'ĐVT', format_border)
        worksheet.write(6, 6, 'SL', format_border)

        worksheet.write(6, 7, 'Đơn giá', format_border)
        worksheet.write(6, 8, 'Thành tiền', format_border)
        worksheet.write(6, 9, 'Ghi chú', format_border)

        begin_row = 7
        arr_seq = []
        stt = 1

        table_total_km = table_total_qty = table_total_amount = 0.0

        for index, item in enumerate(vehicle_dict):

            worksheet.merge_range(begin_row, 0, begin_row + item['count'], 0, stt, format_border)
            worksheet.merge_range(begin_row, 1, begin_row + item['count'], 1, item['vehicle'], format_border)

            arr_seq.append(begin_row)

            row_count = arr_seq[index]
            lines_total_km = lines_total_qty = lines_total_amount = 0
            
            header_row = begin_row

            for line in data_list:
                if item['vehicle'] == line['number']:
                    worksheet.write(row_count + 1, 2, line['destination'], format_border)
                    worksheet.write(row_count + 1, 3, line['content'], format_border)
                    
                    km_total = 0
                    if line['start_km'] and line['end_km']:
                        start_km = convert_number(line['start_km'])
                        end_km = convert_number(line['end_km'])
                        if start_km < end_km:
                            km_total = end_km - start_km

                    worksheet.write(row_count + 1, 4, Cal.convert_dot(km_total), format_border)
                    worksheet.write(row_count + 1, 5, '', format_border)

                    petrol_liter = cal_liter_on_km(km_total, line['id'])
                    crane_liter = Cal.crane_liter(line['crane_hour'], line['id'], 'crane')
                    generator_firing_liter = Cal.crane_liter(line['generator_firing_hour'], line['id'], 'no crane')

                    liter_total = petrol_liter + crane_liter + generator_firing_liter

                    worksheet.write(row_count + 1, 6, Cal.convert_dot(liter_total), format_border)

                    worksheet.write(row_count + 1, 7, Cal.convert_dot(line['price']), format_border)

                    amount_total = 0
                    if line['price']:
                        amount_total = liter_total * line['price']

                    worksheet.write(row_count + 1, 8, Cal.convert_dot(amount_total), format_border)

                    worksheet.write(row_count + 1, 9, line['note'] if line['note'] != 'None' else '', format_border)

                    lines_total_km += km_total
                    lines_total_qty += liter_total
                    lines_total_amount += amount_total

                    row_count += 1
            
            worksheet.write(header_row, 2, '', format_title)
            worksheet.write(header_row, 3, 'Phục vụ BQLDA', format_title)
            worksheet.write(header_row, 4, Cal.convert_dot(lines_total_km), format_title)
            worksheet.write(header_row, 5, 'Lít', format_title)
            worksheet.write(header_row, 6, Cal.convert_dot(lines_total_qty), format_title)
            worksheet.write(header_row, 7, '', format_title)
            worksheet.write(header_row, 8, Cal.convert_dot(lines_total_amount), format_title)
            worksheet.write(header_row, 9, '', format_title)

            table_total_km += lines_total_km
            table_total_amount += lines_total_amount

            stt += 1
            begin_row = begin_row + item['count'] + 1
        
        worksheet.write(begin_row, 0,'', format_title)
        worksheet.write(begin_row, 1,'Tổng cộng: ', format_title)
        worksheet.write(begin_row, 2,'', format_title)
        worksheet.write(begin_row, 3, '', format_title)
        worksheet.write(begin_row, 4, Cal.convert_dot(table_total_km), format_title)
        worksheet.write(begin_row, 5, '', format_title)
        worksheet.write(begin_row, 6, '', format_title)
        worksheet.write(begin_row, 7, '', format_title)
        worksheet.write(begin_row, 8, Cal.convert_dot(table_total_amount), format_title)
        worksheet.write(begin_row, 9, '', format_title)

        worksheet.write(begin_row + 1, 2, 'Bằng chữ:', format1)
        
        n2w_string = ''
        if table_total_amount > 0:
            n2w_string = n2w(str(round(table_total_amount))).capitalize()
            n2w_string = n2w_string + ' đồng.'
        worksheet.merge_range(begin_row + 1, 3, begin_row + 1, 9, n2w_string, format1)

        worksheet.merge_range(begin_row + 2, 0, begin_row + 2, 3, 'VĂN PHÒNG', format1)
        worksheet.merge_range(begin_row + 2, 4, begin_row + 2, 7, 'NGƯỜI LẬP', format1)

        workbook.close()
        return response

    else:
        return redirect('/vehicle/unexpected_error/')

class VehicleWorkingStageView(View):
    def get(self, request):
        try:
            calendar_id = request.GET['cid']
            vehicle_id = request.GET['vid']

            calendar = VehicleWorkingStage.objects.filter(calender=calendar_id, vehicle=vehicle_id).first()
            
            vehicle_calender = ModelVehicleCalender.objects.get(id=calendar_id)
            vehicle_type = vehicle_calender.vehicle_type
            
            is_crane = False
            if vehicle_type:
                is_left_tab = vehicle_type.is_left_tab
                if not is_left_tab:
                    is_crane = True
            
            disabled_confirm_btn = False
            disabled_save_btn = False

            if not request.user.has_perm("vehicle.driver_vehicle"):
                disabled_save_btn = True

            if calendar:
                form = VehicleWorkingStageForm(instance=calendar)   
                disabled_confirm_btn = _check_validate(calendar, is_crane)      
            else:
                form = VehicleWorkingStageForm(initial={
                    'vehicle': vehicle_id
                })
            
            if request.user.is_active and request.user.is_superuser:
                has_perm_work_perform = True
            else:
                has_perm_work_perform = check_perm_work_perform(request.user.id, calendar_id)

            context = {
                'form': form, 
                'cid': calendar_id, 
                'vid': vehicle_id,
                'is_crane': is_crane,
                'disabled_save_btn': disabled_save_btn,
                'disabled_confirm_btn': disabled_confirm_btn,
                'has_perm_work_perform': has_perm_work_perform,
                'confirm_statuses': [status[0] for status in VehicleWorkingStage.STATUS if status[0] != 'NEW']
            }
            return render(request, "vehicle/vehicle_stage_modal_view.html", context)
        except Exception as exc:
            print(exc)
            LoggingFile(exc)
            return redirect('/vehicle/unexpected_error/')
    
    def post(self, request):
        try:
            user_id = request.user
            calendar_id = request.GET['cid']
            vehicle_id = request.GET['vid']
            calendar_record = ModelVehicleCalender.objects.get(id=calendar_id)
            calendar = VehicleWorkingStage.objects.filter(calender=calendar_id, vehicle=vehicle_id).first()
            
            if request.method == 'POST':
                if calendar:
                    start_odo_image_url = end_odo_image_url = False
                    if calendar.start_odo_image:
                        start_odo_image_url = calendar.start_odo_image.url
                    if calendar.end_odo_image:
                        end_odo_image_url = calendar.end_odo_image.url

                    form = VehicleWorkingStageForm(request.POST, request.FILES, instance=calendar)
                    
                    if form.is_valid() and form.has_changed():
                        # Remove image out dir
                        query_dict = dict(form.data)
                        if query_dict.get('start_odo_image-clear', False):
                            if len(query_dict.get('start_odo_image-clear')) == 1 and query_dict.get('start_odo_image-clear')[0] == 'on':
                                if '/files' in start_odo_image_url:
                                    start_odo_image_url = start_odo_image_url.replace('/files', '')
                                    remove_image(start_odo_image_url)

                        if query_dict.get('end_odo_image-clear', False):
                            if len(query_dict.get('end_odo_image-clear')) == 1 and query_dict.get('end_odo_image-clear')[0] == 'on':
                                if '/files' in end_odo_image_url:
                                    end_odo_image_url = end_odo_image_url.replace('/files', '')
                                    remove_image(end_odo_image_url)
                        
                        post = form.save(commit=False)
                        post.write_uid = user_id
                        post.write_date = datetime.now()
                        post.fuel_type = self.get_fuel_type(calendar_id)
                        post.save()
                else:
                    form = VehicleWorkingStageForm(request.POST, request.FILES)
                    post = form.save(commit=False)
                    post.create_uid = user_id
                    post.create_date = datetime.now()
                    post.calender = calendar_record
                    post.fuel_type = self.get_fuel_type(calendar_id)
                    post.save()

            return redirect(request.environ['HTTP_REFERER'])
        except Exception as exc:
            print(exc)
            LoggingFile(exc)
            return HttpResponse("false")

    def get_fuel_type(self, cid):
        divided_vehicle = Vehicle_Division.objects.filter(calender=cid).first()
        if divided_vehicle:
            if divided_vehicle.vehicle:
                if divided_vehicle.vehicle.vehicle_type:
                    fuel_type = divided_vehicle.vehicle.fuel_type
                    return fuel_type
        return None


def _check_validate(record, is_crane):
    check_valid = False
    check_crane = False

    if is_crane == True:
        if record.crane_hour and record.generator_firing_hour:
            check_crane = True

    if record.start_km and record.start_odo_image and record.end_km and record.end_odo_image:
        check_valid = True
    
    return check_valid

def stage_confirm_action(request):
    try:
        if request.method == 'POST':
            sid = request.POST['stage_id']
            status = request.POST['status']

            approver_id = request.user

            record = VehicleWorkingStage.objects.get(id=sid)
            
            check_valid = _check_validate(record, False)

            has_perm_driver = request.user.has_perm("vehicle.driver_vehicle")            
            has_perm_register = request.user.has_perm("vehicle.register_vehicle")

            if not check_valid:
                return HttpResponse("no_valid")

            if has_perm_register:
                if status == "NEW":
                    VehicleWorkingStage.objects.filter(id=sid, status="NEW").update(status="CONFIRM", approved_by=approver_id)
                    return HttpResponse("true")
                elif status == "CONFIRM":
                    VehicleWorkingStage.objects.filter(id=sid, status="CONFIRM").update(status="NEW")
                    return HttpResponse("cancel")
                else:
                    return HttpResponse("false")
            else:
                return HttpResponse("no_perm")

    except Exception as exc:
        print(exc)
        return HttpResponse("false")

def remove_image(image_path):
    try:
        path = settings.MEDIA_ROOT + image_path
        exist = os.path.exists(path)
        if exist:
            os.remove(path)
    except ValueError as e:
        print('ValueError: ', e)

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

            vehicle = ModelVehicleCalender.objects.get(id=calender_id)
            week_calender = vehicle.calender

            if not week_calender:
                AssignModel = AssignedUser
                MainCalenderModel = ModelVehicleCalender
                _id = calender_id
            else:
                AssignModel = Working_Division
                MainCalenderModel = Calender
                _id = week_calender.id

            # If user do not exist in db then INSERT 2 table, otherwise then UPDATE
            for user in users_check:
                # filter() can use id and get() must be instance of class
                if AssignModel.objects.filter(calender=_id, user=int(user)).exists() == False:
                    # print("======INSERT=============")
                    insert = AssignModel(calender=MainCalenderModel.objects.get(id=_id), user=User.objects.get(id=user), active=True, create_uid=request.user)
                    insert.save()
                else:
                    # print("======UPDATE==============")
                    AssignModel.objects.filter(calender=_id, user=int(user)).update(active=True, write_uid=user_id, write_date=datetime.now())  
            # If user that not check exists in db then update active
            for user in users_no_check:
                if AssignModel.objects.filter(calender=_id, user=int(user)).exists() == True:
                    # print("==================UPDATE NO ACTIVE===================")
                    AssignModel.objects.filter(calender=_id, user=int(user)).update(active=False, write_uid=user_id, write_date=datetime.now())  
                
            return HttpResponse("true")

    except Exception as exc:
        print(exc)
        return HttpResponse("false")
    
def check_perm_work_perform(user_id, vc_id):
    try:
        record = ModelVehicleCalender.objects.get(id=vc_id)

        # If record has week calender
        assigned_calender = []

        if record.calender:
            if hasattr(record.calender, 'id'):
                c_id = record.calender.id
                assigned_calender = Working_Division.objects.filter(calender=c_id)
        else:
            assigned_calender = AssignedUser.objects.filter(calender=vc_id)
        
        assigned_user_list = [item.user.id for item in assigned_calender if item.user]

        if user_id in assigned_user_list:
            return True

        return False

    except Exception as exc:
        print(exc)
        LoggingFile(exc)
        return None