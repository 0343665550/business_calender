django.jQuery( document ).ready(function() {
    var vehicle_type = django.jQuery('#id_vehicle_type').val();
    var vehicle_type_text = django.jQuery('#id_vehicle_type option:selected').text();
    if (vehicle_type == "" || vehicle_type_text == "Xe con") {
        django.jQuery('.field-crane_fuel_rate').attr('style','display:none;');
        django.jQuery('.field-generator_firing_fuel_rate').attr('style', 'display: none;');
    }

    // Selecting one in two option position of calender
    django.jQuery('#id_vehicle_type').change(function(){
        var value = django.jQuery('#id_vehicle_type').val();
        var text = django.jQuery('#id_vehicle_type option:selected').text();
        if(value == "" || text == "Xe con") {
            django.jQuery('.field-crane_fuel_rate').attr('style','display:none;');
            django.jQuery('.field-generator_firing_fuel_rate').attr('style', 'display: none;');
        } else {
            django.jQuery('.field-crane_fuel_rate').removeAttr('style');
            django.jQuery('.field-generator_firing_fuel_rate').removeAttr('style');
        }
        
    });
});