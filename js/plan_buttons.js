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

$(document).ready(function() {
    init_plan_buttons();

    $("a.plan-click").click(function(){
        var pid=$(this).attr("data-pid");
        var val=$(this).attr("id");
        $.post("/updateplan",
                    {
                        val: $(this).attr("id"),
                        gid: $(this).attr("data-gid"),
                        mid: $(this).attr("data-mid"),
                        bid: $(this).attr("data-bid")
                    },
                    function(responseTxt,statusTxt,xhr){
                        if(statusTxt=="success")
                            set_plan_button("plan-"+pid,val)
                        if(statusTxt=="error")
                          alert("Error: "+xhr.status+": "+xhr.statusText);
                    });
    });
});


