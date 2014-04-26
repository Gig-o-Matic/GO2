function update_comment(gk) {
    $.post("/gig_get_comment",
                {
                    gk: gk,
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        $('#gig_comment').html(responseTxt)
                    if(statusTxt=="error")
                        alert("Error: "+xhr.status+": "+xhr.statusText);
                });
}

function add_comment(gk) {
    var d = new Date();
    offset=d.getTimezoneOffset()/60;
    $.post("/gig_add_comment",
                {
                    gk: gk,
                    c: $('#commentinput').val(),
                    o: offset
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        $('#commentinput').val('');
//                         $('#gig_comment').html(responseTxt)
                        update_comment(gk);
                    if(statusTxt=="error")
                        alert("Error: "+xhr.status+": "+xhr.statusText);
                });
    
}
