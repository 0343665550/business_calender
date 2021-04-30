$(document).ready(function () {
    // $('input[type="checkbox"]').next('label').remove();
    // Is used to click on span tag then checkbox input active
    // Not use label tag cuz jet lib
    $('.check_label').on('click', function () {
        let user_id = $(this).attr("id_");
        // let is_check = false;
        // $.each($("input[id_="+user_id+"]:checked"), function(){
        let is_check = $("input[id_="+user_id+"]").prop("checked");
        // });
        // alert(is_check);
        $("input[id_="+user_id+"]").attr('checked', !is_check);
    })
    $('.btn_division').on('click', function () {

        var calender_id = $(this).attr("data");
        var chair_unit_id = $("#chair_unit_id").val();
        var date = document.forms["myform"]["theDate2"].value;
        // List users that are checked
        var listIdUser = [];
        $.each($("input[name='is_check"+calender_id+"']:checked"), function(){
            listIdUser.push($(this).val());
        });
        // List users that aren't checked
        var listIdUser_NoCheck = [];
        $.each($("input[name='is_check"+calender_id+"']:not(:checked)"), function(){
            listIdUser_NoCheck.push($(this).val());
        });
        // console.log(listIdUser);
        // console.log(calender_id, chair_unit_id, date);
        // console.log(listIdUser_NoCheck);
        // if (listIdUser.length > 0) {
        $.ajax({
            url: "/calender/confirm_division/",
            type: "POST", 
            data:
            {
                json_data: JSON.stringify({ 
                    'users_check': listIdUser,
                    'users_no_check' : listIdUser_NoCheck,
                    'calender_id': calender_id,
                    'chair_unit_id': chair_unit_id,
                    'date': date
                })
            },
            headers: {'X-CSRFToken': $("input[name='csrfmiddlewaretoken']").val()}, 
            success: function(data) {
                $('#myModalDivision'+calender_id).modal('hide');
                if (data == "false") {
                    Swal.fire("Rất tiếc!", "Phân công dự họp thất bại!", "warning");
                } else {
                    // Swal.fire("Chúc mừng!", "Phân công dự họp thành công!", "success");
                    // Thay thế table content
                    $("#filter").replaceWith(data);
                }
            },
            error: function(xhr, status, error){
                var errorMessage = xhr.status + ': ' + xhr.statusText
                alert('Sorry - ' + errorMessage);
            }
        });
        // } else {
        //     Swal.fire("Rất tiếc!", "Vui lòng chọn người được phân công!", "warning");
        // }
    });
})