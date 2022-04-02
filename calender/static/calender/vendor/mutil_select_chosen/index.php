<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Page Title</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="bootstrap/css/bootstrap.min.css">
    <link rel="stylesheet" href="chosen/chosen.css">
    <style>
        #output {
        padding: 20px;
        background: #dadada;
        }

        form {
        margin-top: 20px;
        }

        select {
        width: 300px;
        }
    </style>
</head>
<body>
    <div id="output" style="display:none;"></div>
    <form method="get">
    <select data-placeholder="Choose tags ..." name="tags[]" multiple class="chosen-select">
        <option value="Engineering">Engineering</option>
        <option value="Carpentry">Carpentry</option>
        <option value="Plumbing">Plumbing</option>
        <option value="Electical">Electrical</option>
        <option value="Mechanical">Mechanical</option>
        <option value="HVAC">HVAC</option>
    </select>
    <input type="submit">
    </form>
    <script src="js/jquery-3.3.1.min.js"></script>
    <script src="bootstrap/js/bootstrap.min.js"></script>
    <script src="chosen/chosen.jquery.js"></script>
    <script>
        document.getElementById('output').innerHTML = location.search;
        $(".chosen-select").chosen();
    </script>
    
</body>
</html>