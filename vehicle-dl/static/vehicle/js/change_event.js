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
    })
})