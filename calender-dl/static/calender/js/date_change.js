django.jQuery( document ).ready(function() {
    // When select date of start then date of end will be filled
    django.jQuery('#id_start_time_1').click(function() {
        var value = django.jQuery("#id_start_time_0").val();
        // alert(value);
        django.jQuery('#id_end_time_0').val(value);
    });
    // Date of end won't less than date of start
    django.jQuery('#id_end_time_1').click(function() {
        var start_date = django.jQuery("#id_start_time_0").val();
        var end_date = django.jQuery("#id_end_time_0").val();
        // console.log(start_date);
        // console.log(end_date);
        if(start_date > end_date) {
            alert("Ngày kết thúc không thể nhỏ hơn ngày bắt đầu");
            django.jQuery("#id_end_time_0").val("");
        }
    });
    // Selecting one in two option position of calender
    django.jQuery('#id_address').change(function(){
        var value = django.jQuery('#id_address').val();
        if(value.length != 0) {
            django.jQuery('#id_location').attr('disabled','disabled');
        }else{
            django.jQuery('#id_location').removeAttr('disabled');
        }
        
    })
    django.jQuery('#id_location').change(function(){
        var value = django.jQuery('#id_location').val();
        var meeting_name = django.jQuery('#id_location option:selected').text();
        var token = django.jQuery('input[name="csrfmiddlewaretoken"]').prop('value');
        // alert(token);
        if(value){
            django.jQuery('#id_address').attr('disabled','disabled');
            // alert(django.jQuery('#id_start_time_0').val())
            var start_date = django.jQuery('#id_start_time_0').val() + ' ' + django.jQuery('#id_start_time_1').val();
            var end_date = django.jQuery('#id_end_time_0').val() + ' ' + django.jQuery('#id_end_time_1').val();
            // alert(start_date.length);
            if (start_date.length == 19 && end_date.length == 19) {
                // alert("19");
                django.jQuery.ajax({
                    url: "/check_double_calender/",
                    type: "POST", 
                    data:
                    {
                        'date1': start_date.substring(0, 16),
                        'date2' : end_date.substring(0, 16),
                        'meeting_id': value,
                        'chair_unit_id': null
                    },
                    headers: {'X-CSRFToken': token}, // for csrf token
                    success: function(data) {
                        if (data.message == 'YES') {
                            // django.jQuery("#id_location option:selected").prop("selected", false);
                            // django.jQuery("#id_location option:first").prop('selected','selected');
                            Swal.fire(
                                'Thông Báo!',
                                // 'Thời gian từ '+start_date+' đến '+end_date+' tại '+meeting_name+' đã được đăng ký lịch.',
                                'Phòng '+meeting_name+' đã được đăng ký lịch vào thời gian này.',
                                'warning'
                            )
                        }
                    }
                })
            }
        }else{
            django.jQuery('#id_address').removeAttr('disabled');
        }
        var start_date = django.jQuery("#id_start_time_0").val();
        var end_date = django.jQuery("#id_end_time_0").val();
        if (start_date == end_date) {
            // alert(start_date);
            var start_time = django.jQuery("#id_start_time_1").val();
            var end_time = django.jQuery("#id_end_time_1").val();
            // alert(start_time);
            // alert(end_time);
            if (start_time > end_time) {
                alert("Thời gian kết thúc không thể nhỏ hơn thời gian bắt đầu");
                django.jQuery("#id_end_time_1").val("");
                end_time = '';
            }
        }
    })
    django.jQuery('#id_chair_unit').change(function(){
        var value = django.jQuery('#id_chair_unit').val();
        var meeting_id = django.jQuery('#id_location').val();
        var unit_name = django.jQuery('#id_chair_unit option:selected').text();
        var token = django.jQuery('input[name="csrfmiddlewaretoken"]').prop('value');
        // alert(token);
        if(value){
            var start_date = django.jQuery('#id_start_time_0').val() + ' ' + django.jQuery('#id_start_time_1').val();
            var end_date = django.jQuery('#id_end_time_0').val() + ' ' + django.jQuery('#id_end_time_1').val();
            
            if (start_date.length == 19 && end_date.length == 19) {
                // alert("19");
                django.jQuery.ajax({
                    url: "/check_double_calender/",
                    type: "POST", 
                    data:
                    {
                        'date1': start_date,
                        'date2' : end_date,
                        'meeting_id': meeting_id,
                        'chair_unit_id': value
                    },
                    headers: {'X-CSRFToken': token}, // for csrf token
                    success: function(data) {
                        if (data.message == 'YES') {

                            Swal.fire(
                                'Thông Báo!',
                                'Thời gian từ '+start_date+' đến '+end_date+', đơn vị '+unit_name+' đã được đăng ký lịch.',
                                'warning'
                            )
                        }
                    }
                })
            }
        }
    });
    var length_choice = django.jQuery(".field-content_ids").find(".select2-selection--multiple ul").children(".select2-selection__choice");
    if (length_choice.length > 0) {
        django.jQuery('#id_content').attr('disabled','disabled');
    }
    // Disable another fieled when input one field
    django.jQuery("#id_content_ids").change(function () {
        var value = django.jQuery('#id_content_ids option:selected').text();
        if(value.length != 0) {
            django.jQuery('#id_content').attr('disabled','disabled');
        }else{
            django.jQuery('#id_content').removeAttr('disabled');
        }
    });
    django.jQuery("#id_content").change(function () {
        var value = django.jQuery('#id_content').val();
        if(value.length != 0) {
            django.jQuery('#id_content_ids').attr('disabled','disabled');
        }else{
            django.jQuery('#id_content_ids').removeAttr('disabled');
        }
    })
    django.jQuery("#id_start_time_0").attr("autocomplete", "off");
    django.jQuery("#id_start_time_1").attr("autocomplete", "off");
    django.jQuery("#id_end_time_0").attr("autocomplete", "off");
    django.jQuery("#id_end_time_1").attr("autocomplete", "off");
    django.jQuery("#id_content").attr("rows", "2");
    django.jQuery("#id_other_component").attr("rows", "2");
    django.jQuery("#id_other_prepare").attr("rows", "2");
    django.jQuery(".vLargeTextField").attr("cols", 10);
    django.jQuery(".vLargeTextField").css("font-size", 14);
    django.jQuery(".select2-selection--multiple").attr("style", "width: 350px");
    django.jQuery("#id_content").attr("style", "width: 350px");
    // django.jQuery("#id_join_component").attr('disabled', true);
    // console.log("JOIN COMPONENT");

    // django.jQuery(".field-is_active").replaceWith('<h3 class="icon-cross"></h3>');

    // django.jQuery("#multiplefile_set-0 .delete").append('<div><a class="inline-deletelink-0" href="#">Gỡ bỏ</a></div>');
});