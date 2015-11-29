function update_forum(gk) {
    $.post("/gig_get_forumpost",
                {
                    gk: gk,
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        $('#gig_forum').html(responseTxt)
                    if(statusTxt=="error")
                        alert("Error: "+xhr.status+": "+xhr.statusText);
                });
}

function add_forumpost(gk) {
    var d = new Date();
    offset=d.getTimezoneOffset()/60;
    $.post("/gig_add_forumpost",
                {
                    gk: gk,
                    c: $('#forumpostinput').val(),
                    o: offset
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        $('#forumpostinput').val('');
//                         $('#gig_forum').html(responseTxt)
                        update_forum(gk);
                    if(statusTxt=="error")
                        alert("Error: "+xhr.status+": "+xhr.statusText);
                });
    
}
