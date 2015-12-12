
function update_forum_topics(fk) {
    $.post("/forum_all_topics",
                {
                    fk: fk,
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        $('#forum_topics').html(responseTxt)
                    if(statusTxt=="error")
                        alert("Error: "+xhr.status+": "+xhr.statusText);
                });
}

function update_forum_posts(tk) {
    $.post("/topic_get_forumpost",
                {
                    tk: tk,
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        $('#gig_forum').html(responseTxt)
                    if(statusTxt=="error")
                        alert("Error: "+xhr.status+": "+xhr.statusText);
                });
}

function add_forumpost(tk) {
    var d = new Date();
    $.post("/topic_add_forumpost",
                {
                    tk: tk,
                    c: $('#forumpostinput').val()
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        $('#forumpostinput').val('');
//                         $('#gig_forum').html(responseTxt)
                        update_forum_posts(tk);
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

