// CODE FOR PLAN BUTTONS
function set_plan_button(the_id, the_value) {

    var the_result='<i class="fa fa-minus fa-sm" style="color:black"></i>'

    switch(the_value) {
        case '1':
            the_result='<i class="fas fa-circle" style="color:green"></i>'
            break;
        case '2':
            the_result='<i class="far fa-circle" style="color:green"></i>'
            break;
        case '3':
            the_result='<i class="fas fa-question" style="color:gray"></i>'
            break;
        case '4':
            the_result='<i class="far fa-square" style="color:red"></i>'
            break;
        case '5':
            the_result='<i class="fas fa-square" style="color:red"></i>'
            break;
        case '6':
            the_result='<i class="fas fa-times" style="color:black"></i>'
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
    document.getElementById(pk).innerHTML='<i class="fa fa-spinner fa-spin fa-lg"></i>';
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

// CODE FOR FEEDBACK BUTTONS
function init_feedback_buttons() {
    plan_buttons=document.getElementsByClassName('feedback-button');  
    for (var i=0; i < plan_buttons.length; i++) {
        val = plan_buttons[i].getAttribute("data-init")
        set_feedback_button(plan_buttons[i].id, val);
    }
}    

function set_feedback_button(the_id, the_value) {
    if (the_value=='') {
        val = '<i class="fas fa-minus fa-sm" style="color:black"></i>'
    } else {
        val = the_value
    }
    document.getElementById(the_id).innerHTML=val;
}

function update_feedback(pk, val) {
    document.getElementById('ef-'+pk).innerHTML='<i class="fa fa-spinner fa-spin fa-lg"></i>';
    $.post("/updateplanfeedback",
                {
                    val: val,
                    pk: pk
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        set_feedback_button("ef-"+pk, responseTxt)
                    if(statusTxt=="error")
                      alert("Error: "+xhr.status+": "+xhr.statusText);
                });
}



// CODE FOR SELECTING SECTIONS
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


// CODE FOR COMMENTS ON AGENDA PAGE
function show_comment(the_plan) {
    $('#comment-init-'+the_plan).hide();
    $('#comment-row-'+the_plan).show();
    setTimeout(function(){
        $('#comment-'+the_plan).click();
    }, 100);
}

function closed_comment(thing) {
    if ($('#comment-'+thing).text()=='') {
        $('#comment-init-'+thing).show();
        $('#comment-row-'+thing).hide();
    }
}


$(document).ready(function() {
    init_plan_buttons();
    init_feedback_buttons();
    $('.comment-thing').editable({
        emptytext: '<i class="far fa-comment"></i>',
        emptyclass: 'empty-comment',
        mode: 'inline',
    }).on('hidden', function(e, reason) {
        closed_comment(e.target.getAttribute('data-pk'));
    })
});

