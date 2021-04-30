// Set check or unchecked all checkboxes
function checkAllRight(e) {
    var checkboxes = document.getElementsByName('check_right');
    if (e.checked) {
        for (var i = 0; i < checkboxes.length; i++) { 
            checkboxes[i].checked = true;
        }
    } else {
        for (var i = 0; i < checkboxes.length; i++) {
            checkboxes[i].checked = false;
        }
    }
}

//deselect "checked all", if one of the listed checkbox product is unchecked amd select "checked all" if all of the listed checkbox product is checked
$('.checkbox_right').change(function(){ //".checkbox" change 
    if($('.checkbox_right:checked').length == $('.checkbox_right').length){
        $('.checked_all_right').prop('checked', true);
    }else{
        $('.checked_all_right').prop('checked', false);
    }
});

$(document).ready(function () {
    // Action approval "DUYỆT XE"
    $('#btn_approval_right').click(function() { 
        var listIdCalender = [];
        $.each($("input[name='check_right']:checked"), function(){
            listIdCalender.push($(this).val());
        });
        var countChecked = $('.checkbox_right:checked').length;
        // console.log(countChecked);
        
        if (countChecked == 0) {
            Swal.fire(
                'Thông báo!',
                'Chọn lịch xe để duyệt nhé!',
                'warning'
            )
        } else {
            if (listIdCalender.length === 0) {
                Swal.fire(
                    'Thông báo!',
                    'Bạn phải chọn lịch xe để duyệt chứ!!',          
                    'warning'
                )
            } else {
                $.ajax({
                    url: '/vehicle/vehicle_calender/approval/',
                    type: 'POST',
                    data:
                    {
                        json_data: JSON.stringify({ 'cid_list': listIdCalender })
                    },
                    headers: {'X-CSRFToken': $("input[name='csrfmiddlewaretoken']").val()}, 
                    success: function (resp) {
                        if (resp == "true") {
                            Swal.fire(
                                'Duyệt!',
                                'Bạn đã duyệt thành công!',
                                'success'
                            )
                            location.reload();
                        } else {
                            Swal.fire(
                                'Sorry!',
                                'Bạn đã duyệt không thành công!',
                                'warning'
                            )
                        }
                    },
                    error: function(xhr, status, error){
                        var errorMessage = xhr.status + ': ' + xhr.statusText
                        alert('Error - ' + errorMessage);
                    }
                });
            }
        }
    });
})