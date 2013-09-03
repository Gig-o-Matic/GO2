function set_plan_button(the_id, the_value) {

    var the_result='<i class="icon-circle-blank icon-large" style="visibility:hidden"></i><i class="icon-question-sign icon-large" style="color:black"></i>'

    switch(the_value) {
        case '1':
            the_result='<i class="icon-plus-sign icon-large" style="color:green"></i><i class="icon-plus-sign icon-large" style="color:green"></i>'
            break;
        case '2':
            the_result='<i class="icon-circle-blank icon-large" style="visibility:hidden"></i><i class="icon-plus-sign icon-large" style="color:green"></i>'
            break;
        case '3':
            the_result='<i class="icon-plus-sign icon-large" style="color:green"></i><i class="icon-minus-sign icon-large" style="color:red"></i>'
            break;
        case '4':
            the_result='<i class="icon-circle-blank icon-large" style="visibility:hidden"></i><i class="icon-minus-sign icon-large" style="color:red"></i>'
            break;
        case '5':
            the_result='<i class="icon-minus-sign icon-large" style="color:red"></i><i class="icon-minus-sign icon-large" style="color:red"></i>'
            break;
    }
    
    document.getElementById(the_id).innerHTML=the_result;
}

var plan_buttons_to_initialize=new Array()
var plan_buttons_init_val=new Array()

function add_plan_button(pid,val) {
    plan_buttons_to_initialize.push(pid);
    plan_buttons_init_val.push(val);
}

function init_plan_buttons() {
    console.log('in init plan buttons');
    for (var i=0; i < plan_buttons_to_initialize.length; i++) {
        set_plan_button(plan_buttons_to_initialize[i], plan_buttons_init_val[i]);
    }
}    

$(document).ready(function() {
    init_plan_buttons();
    $("a.plan-click").click(function(){
        var pk=$(this).attr("data-pk");
        var prefix=$(this).attr("data-prefix");
        var val=$(this).attr("id");
        $.post("/updateplan",
                    {
                        val: val,
                        pk: pk
                    },
                    function(responseTxt,statusTxt,xhr){
                        if(statusTxt=="success")
                            set_plan_button("plan-"+prefix+pk,val)
                        if(statusTxt=="error")
                          alert("Error: "+xhr.status+": "+xhr.statusText);
                    });
    });
});


