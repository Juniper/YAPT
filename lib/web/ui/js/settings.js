/*
DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
Copyright (c) 2018 Juniper Networks, Inc.
All rights reserved.
Use is subject to license terms.

Author: cklewar
*/

function openSetting(evt, settingName) {

    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");

    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    tablinks = document.getElementsByClassName("tablinks");

    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    document.getElementById(settingName).style.display = "block";
    loadSettingConfigurationElements('YAPT');
    evt.currentTarget.className += " active";
}

// Get the element with id="defaultOpen" and click on it
document.getElementById("defaultOpen").click();

function loadSettingConfigurationElements(settingName){

    console.log('inside');

    function fetch() {
        $.ajax({
            url: '/api/settings',
            type: 'GET',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=json&name=' + settingName,
            success: function (response) {

                data = jQuery.parseJSON(response);

                if (data[0]){

                    cfg = jQuery.parseJSON(data[1]);
                    console.log(cfg);
                }
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}