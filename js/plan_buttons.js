function set_plan_button(the_id, the_value) {

    var the_result='<i class="fa fa-minus fa-sm" style="color:black"></i>'

    switch(the_value) {
        case '1':
            the_result='<i class="fa fa-circle fa-lg" style="color:green"></i>'
            break;
        case '2':
            the_result='<i class="fa fa-circle-o fa-lg" style="color:green"></i>'
            break;
        case '3':
            the_result='<i class="fa fa-question fa-lg" style="color:gray"></i>'
            break;
        case '4':
            the_result='<i class="fa fa-square-o fa-lg" style="color:red"></i>'
            break;
        case '5':
            the_result='<i class="fa fa-square fa-lg" style="color:red"></i>'
            break;
    }
    
    document.getElementById(the_id).innerHTML=the_result;
}

function init_plan_buttons() {
    plan_buttons=document.getElementsByClassName('plan-button');  
    for (var i=0; i < plan_buttons.length; i++) {
        set_plan_button(plan_buttons[i].id, plan_buttons[i].getAttribute("data-init"));
    }
}    

function update_plan(pk, val) {
    $.post("/updateplan",
                {
                    val: val,
                    pk: pk
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        set_plan_button(pk,val)
                    if(statusTxt=="error")
                      alert("Error: "+xhr.status+": "+xhr.statusText);
                });
}

function section_select(pk, sk, name) {
    $.post("/updateplansection",
                {
                    sk: sk,
                    pk: pk
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        $('#sel-'+pk).html(name+ " <span class='caret'></span>")
                    if(statusTxt=="error")
                      alert("Error: "+xhr.status+": "+xhr.statusText);
                });
}

$(document).ready(function() {
    init_plan_buttons();
    $('.comment-thing').editable({
        emptytext: '<i class="fa fa-comment-o"></i>',
        emptyclass: 'empty-comment',
        mode: 'inline'
    });
});

