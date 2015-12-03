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

function add_forumpost(pk, gk) {
    var d = new Date();
    $.post("/gig_add_forumpost",
                {
                    pk: pk,
                    gk: gk,
                    c: $('#forumpostinput').val()
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

function open_post_reply(pk, gk) {
    $.post("/open_post_reply",
                {
                    pk: pk,
                    gk: gk
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        $('#pr-'+pk).html(responseTxt)
                    if(statusTxt=="error")
                        alert("Error: "+xhr.status+": "+xhr.statusText);
                });
    
}
