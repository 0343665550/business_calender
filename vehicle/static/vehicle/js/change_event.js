django.jQuery(document).ready(function () {
    django.jQuery("#id_note").attr("rows", "2");
    let vehicleType = django.jQuery("#id_vehicle_type").val();
    if (vehicleType == 1) {
        django.jQuery("#id_expected_km").val("");
        django.jQuery("#id_expected_crane_hour").val("");
        django.jQuery("#id_expected_km").attr('disabled', 'disabled');
        django.jQuery("#id_expected_crane_hour").attr('disabled', 'disabled');
    }
    django.jQuery("#id_vehicle_type").change(function () {
        let vehicle_type = django.jQuery("#id_vehicle_type").val();
        // If it's "Xe con" then disabled two fields 
        if (vehicle_type == 1) {
            django.jQuery("#id_expected_km").val("");
            django.jQuery("#id_expected_crane_hour").val("");
            django.jQuery("#id_expected_km").attr('disabled', 'disabled');
            django.jQuery("#id_expected_crane_hour").attr('disabled', 'disabled');
        } else {
            django.jQuery("#id_expected_km").removeAttr('disabled');
            django.jQuery("#id_expected_crane_hour").removeAttr('disabled');
        }
    });
    // Event when click "Lãnh đạo duyệt" checkbox in create functionality
    if (django.jQuery("input[id='id_is_appr_manager']").prop("checked")) {
        django.jQuery(".field-managers").attr("style", "");
    }
    django.jQuery("#id_is_appr_manager").on('click', function () {
        if (django.jQuery("input[id='id_is_appr_manager']").prop("checked")) {
            django.jQuery(".field-managers").attr("style", "");
        } else {
            django.jQuery(".field-managers").attr("style", "display:none;");
        }
    })

})