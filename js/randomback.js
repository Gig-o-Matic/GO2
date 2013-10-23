$(document).ready(function() {
    var bgs = new Array();
    bgs[0] = 'url(/images/tuba.png)';
    bgs[1] = 'url(/images/bone.png)';
    bgs[2] = 'url(/images/tpt.png)';
    $(".landingwrap").css('background-image',bgs[Math.floor(Math.random()*bgs.length)]);
});