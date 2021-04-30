    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
    var yyyy = today.getFullYear();

    // Get first day of week
    var first = new Date(today.setDate(today.getDate() - today.getDay() + 1));
    var firstday = first.getMonth() + 1 + '-' + first.getDate() + '-' + first.getFullYear();
    // Get current date
    
    // console.log('first of this week: ', firstday);
    today = mm + '-' + dd + '-' + yyyy;
    // console.log(today);
    // Initial 2 array
    var arr_dmy = [];
    var arr_mdy = [];
    var arr_collapse_date = [];
    $("div .collapse").each(function () {
        var id = $(this).attr('id')
        // console.log($(this).attr('id'));
        arr_dmy.push(id);
        arr_day = id.split("-");
        arr_mdy.push(arr_day[1]+'-'+arr_day[0]+'-'+arr_day[2]);
    });
    // console.log(arr_dmy);
    // console.log(arr_mdy);

    // Nếu ngày trong tuần nhỏ hơn ngày hiện tại thì push vào array để removeClass 'show'
    for (let index = 0; index < arr_mdy.length; index++) {
        // if (new Date(arr_mdy[index]) < new Date(today) && new Date(arr_mdy[index]) >= new Date(firstday)) {
            if (new Date(arr_mdy[index]) < new Date(today) ) {
            // arr_collapse_date.push(arr_mdy[index]);
            arr_collapse_date.push(arr_dmy[index]);
            $("#"+arr_dmy[index]).removeClass("show");
        }
    }
    // console.log(arr_collapse_date);