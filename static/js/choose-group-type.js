$(document).ready(function(){
    $('#id_type').change(function(){
        choose_type();
    })
    .change();
});


function choose_type(){
    if ($('#id_type').val() == 1 || $('#id_type').val() == 3 || $('#id_type').val() == 4) {
        $('div.field-report_types').hide();
        $('div.field-administration_areas').show();
        $('#id_administration_areas_to').css('height', 218);
    } else if ($('#id_type').val() == 2 || $('#id_type').val() == 5 || $('#id_type').val() == 6) {
        $('div.field-report_types').show();
        $('div.field-administration_areas').hide();
        $('#id_report_types_to').css('height', 218);
    } else {
        $('div.field-report_types').hide();
        $('div.field-administration_areas').hide();
    }
}