django.jQuery( document ).ready(function() {
    django.jQuery('input:radio[name="addresses"]').change(function() {
        var value = django.jQuery(this).val();
        alert(value);
        if(value == 1){
            django.jQuery('.field-addresses').append('<p>Hello</p>')
        }
    });
});