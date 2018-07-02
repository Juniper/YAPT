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
    loadSettingConfigurationElements(settingName);
    evt.currentTarget.className += " active";
}

// Get the element with id="defaultOpen" and click on it
document.getElementById("defaultOpen").click();

function loadSettingConfigurationElements(settingName){

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
                    settingItems = "<form class=\"form-horizontal\" id=\"formSettings" + settingName + "\">";
                    //console.log(cfg);

                    $.each(cfg, function(i, item) {

                        if (typeof(item) === 'object') {

                            //console.log(jQuery.isArray(item));
                            //console.log(i, item);

                            if (jQuery.isArray(item)) {

                                settingItems = settingItems + "<div class=\"form-group\">" +
                                    "<label for=\"comboBoxSetting" + i + "\" class=\"col-sm-3 control-label\">" + i + "</label>" +
                                    "<div class=\"col-sm-4\">" +
                                        "<select id=\"comboBoxSetting" + i + "\" class=\"form-control comboBox" + i + "\" name=\"comboBoxSetting" + i + "\">" +
                                            "<option value=\"\">Choose Setting</option>" +
                                        "</select>" +
                                    "</div>" +
                                  "</div>";

                                $("#" + settingName).append(settingItems);

                                $.each(item, function( index, value ) {
                                    console.log(index, value);
                                    //console.log($("#comboBoxSetting" + i));
                                    $("#comboBoxSetting" + i).append($("<option></option>").attr("value", index).text(value));
                                    console.log($("#comboBoxSetting" + i));
                                });
                            }

                            //$.each(item, function(j, subitem) {
                                //console.log(j, subitem);
                                //settingItems = settingItems + "<div class=\"form-group\">" +
                                //"<label for=\"input" + i + j +"\" class=\"col-sm-3 control-label\">" + i + ' ' + j + "</label>" +
                                //"<div class=\"col-sm-6\">" +
                                //    "<input type=\"text\" class=\"form-control\" id=\"input" + i + j + "\" placeholder=\""+ i + ' ' + j +"\" value=\"" + subitem + "\">" +
                                //"</div>" +
                            //"</div>";

                            //});

                        } else {
                            settingItems = settingItems + "<div class=\"form-group\">" +
                                "<label for=\"input" + i +"\" class=\"col-sm-3 control-label\">" + i + "</label>" +
                                "<div class=\"col-sm-6\">" +
                                    "<input type=\"text\" class=\"form-control\" id=\"input" + i + "\" placeholder=\"" + item + "\" value=\"" + item + "\">" +
                                "</div>" +
                            "</div>";
                        }
                    });

                    if ($("#" + settingName)){
                        $("#" + settingName).empty();
                        $("#" + settingName).append(settingItems);

                   } else {
                        $("#" + settingName).append(settingItems);
                   }

                } else {
                    console.log('Error in getting settings');
                }
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}