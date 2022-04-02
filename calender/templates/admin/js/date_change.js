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
        // alert(value);
        if(value){
            django.jQuery('#id_address').attr('disabled','disabled');
            // alert(django.jQuery('#id_start_time_0').val())
            var start_date = django.jQuery('#id_start_time_0').val() + ' ' + django.jQuery('#id_start_time_1').val();
            var end_date = django.jQuery('#id_end_time_0').val() + ' ' + django.jQuery('#id_end_time_1').val();
            
            if (start_date.length == 16 && end_date.length == 16) {
                //alert("16");
                
            }

            
        }else{
            django.jQuery('#id_address').removeAttr('disabled');
        }
    })
    // django.jQuery('.select2-selection__rendered').click(function(){
    //     // $( "#draft_calender" ).trigger( "click" );
    //     // location.reload();
    // })
    django.jQuery("#id_start_time_0").attr("autocomplete", "off");
    django.jQuery("#id_start_time_1").attr("autocomplete", "off");
    django.jQuery("#id_end_time_0").attr("autocomplete", "off");
    django.jQuery("#id_end_time_1").attr("autocomplete", "off");
    django.jQuery("#id_content").attr("rows", "2");
    django.jQuery("#id_other_component").attr("rows", "2");
    django.jQuery("#id_other_prepare").attr("rows", "2");
    django.jQuery(".vLargeTextField").attr("cols", 10);
    django.jQuery(".vLargeTextField").css("font-size", 14);

    // django.jQuery("#multiplefile_set-0 .delete").append('<div><a class="inline-deletelink-0" href="#">Gỡ bỏ</a></div>');
});