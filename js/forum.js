
function update_forum_topics(fk,p,np) {
    $.post("/forum_get_topics",
                {
                    fk: fk,
                    page: p,
                    np: np
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        $('#forum_topics').html(responseTxt)
                    if(statusTxt=="error")
                        alert("Error: "+xhr.status+": "+xhr.statusText);
                });
}

function update_forum_posts(tk,p,np,all) {
    $.post("/topic_get_forumpost",
                {
                    tk: tk,
                    page: p,
                    np: np,
                    all: all
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        $('#forum_posts').html(responseTxt)
                    if(statusTxt=="error")
                        alert("Error: "+xhr.status+": "+xhr.statusText);
                });
}

function add_forumpost(tk,np) {
    var d = new Date();
    $.post("/topic_add_forumpost",
                {
                    tk: tk,
                    c: $('#forumpostinput').val()
                },
                function(responseTxt,statusTxt,xhr){
                    if(statusTxt=="success")
                        $('#forumpostinput').val('');
//                        update_forum_posts(tk,np,np);
                        window.location.replace(window.location.href + "&last=1")

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

