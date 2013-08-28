$(document).ready(function() {
    $("a.plan-click").click(function(){
        $.post("/updateplan",
                    {
                        gid: $(this).attr("data-gid"),
                        mid: $(this).attr("data-mid"),
                        bid: $(this).attr("data-bid"),
                        pid: $(this).attr("data-pid"),
                        val: $(this).attr("id")
                    },
                    function(responseTxt,statusTxt,xhr){
                        if(statusTxt=="success")
//                          $(the_divname).html(responseTxt)
                        if(statusTxt=="error")
                          alert("Error: "+xhr.status+": "+xhr.statusText);
                    });
    });
});