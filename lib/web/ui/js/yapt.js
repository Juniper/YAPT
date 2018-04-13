/*
DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
Copyright (c) 2018 Juniper Networks, Inc.
All rights reserved.
Use is subject to license terms.
*/

function updateDeviceProvProgress(device){
    //console.log(device.taskProgress, device.taskKey, device.taskKeyState);
    $("#deviceProvProgressBar-" + device.deviceSerial).css("width", device.taskProgress + "%").text(device.taskProgress + "%");
}

function prepend_device_in_table(device){

    var newTaskStatusRow = "";
    device.deviceTasksStates.forEach(function (value, i) {
        if (typeof value[1] === "object") {
            tempRow = "<tr id=" + device.deviceTaskSequence[i] + "><td>" + device.deviceTaskSequence[i] + "</td>" + "<td colspan=\"2\">" + value[1]['taskStateMsg'] +
            "<td><button id=\"configDetail" + device.deviceSerial + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-eye-open\" data-toggle=\"modal\" data-target=\"#modal" + device.deviceSerial + "\"></button>" +
            "</td></tr>";

        } else {
            tempRow = "<tr id=" + device.deviceTaskSequence[i] + "><td>" + device.deviceTaskSequence[i] + "</td>" + "<td colspan=\"2\">" + value[1] +
            "<td><button id=\"configDetail" + device.deviceSerial + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-eye-open\" data-toggle=\"modal\" data-target=\"#modal" + device.deviceSerial + "\"></button>" +
            "</td></tr>";
        }
        newTaskStatusRow = newTaskStatusRow + tempRow;
    });

    var newRow = "<tr id=" + device.deviceSerial + ">" +
                    "<td>" +
                        "<button class=\"btn btn-default btn-xs\" data-toggle=\"collapse\" data-target=\"#data" + device.deviceSerial + "\" class=\"accordion-toggle\">" +
                            "<span class=\"glyphicon glyphicon-tasks\"></span>" +
                        "</button>" +
                    "</td>" +
                    "<td>" + device.deviceName + "</td>" +
                    "<td>" + device.deviceModel + "</td>" +
                    "<td>" + device.deviceSerial + "</td>" +
                    "<td>" + device.softwareVersion + "</td>" +
                    "<td>" + device.deviceIP + "</td>" +
                    "<td>" + device.deviceTimeStamp + "</td>" +
                    "<td>" +
                        "<div class=\"progress\">" +
                            "<div id=\"deviceProvProgressBar-" + device.deviceSerial + "\" class=\"progress-bar progress-bar-custom\" role=\"progressbar\" aria-valuenow=\"" + device.taskProgress + "\" aria-valuemin=\"0\" aria-valuemax=\"100\" style=\"width:" + device.taskProgress + "%\">" +
                                device.taskProgress + "%" +
                            "</div>" +
                        "</div>" +
                    "</td>" +
                "</tr>" +
                "<tr>" +
                    "<td colspan=\"9\" class=\"hiddenRow\">" +
                        "<div class=\"accordian-body collapse\" id=\"data" + device.deviceSerial + "\">" +
                            "<table class=\"table table-hover\" id=\"task" + device.deviceSerial + "\">" +
                                "<thead>" +
                                    "<tr>" +
                                        "<td>Config Source: local" +
                                        "</td>" +
                                        "<td>Connection: " + device.deviceConnection + "</td>" +
                                        "<td>Source Plugin: " + device.deviceSourcePlugin + "</td>" +
                                        "<td>Group: " + device.deviceGroup + "</td>" +
                                    "</tr>" +
                                    "<tr>" +
                                    "<th>Task</th>" + "<th colspan=\"2\">Status</th>" + "<th>Options</th>" +
                                    "</tr>" +
                                "</thead>" +
                                "<tbody>" +
                                    newTaskStatusRow +
                                "</tbody>" +
                            "</table>" +
                        "</div>" +
                    "</td>" +
                "</tr>";
    $("#devices > tbody").prepend(newRow);
    createDevConfigModal(device);
    deviceConfigLoadCfgBtnEventHandler(device);
}

function update_device_in_table(device){

    var rowID = $("#devices").find("tr#" + device.deviceSerial)
    rowID = rowID.index();

    $("#devices").children('tbody').children().eq(rowID).children().eq(1).text(device.deviceName);
    $("#devices").children('tbody').children().eq(rowID).children().eq(2).text(device.deviceModel);
    $("#devices").children('tbody').children().eq(rowID).children().eq(3).text(device.deviceSerial);
    $("#devices").children('tbody').children().eq(rowID).children().eq(4).text(device.softwareVersion);
    $("#devices").children('tbody').children().eq(rowID).children().eq(5).text(device.deviceIP);
    $("#devices").children('tbody').children().eq(rowID).children().eq(6).text(device.deviceTimeStamp);
    $("#devices").children('tbody').children().eq(rowID).children().eq(8).children().text(device.deviceStatus);
    $("#textarea" + device.deviceSerial).val(device.deviceConfiguration);
    updateDeviceProvProgress(device);
}

function update_device_task_state_in_table(device){

        $("#task" + device.deviceSerial + " tbody #" + device.taskName + " td:nth-child(2)").hide();
        $("#task" + device.deviceSerial + " tbody #" + device.taskName + " td:nth-child(2)").fadeIn("slow");
        $("#task" + device.deviceSerial + " tbody #" + device.taskName + " td:nth-child(2)").text(device.taskState.taskStateMsg);
}

function update_dev_and_reset_task_state(device){

    update_device_in_table(device)
    $("#task" + device.deviceSerial + " tbody tr td:nth-child(2)").each(function(i) {
            $(this).text('Waiting');
    });

    $("#" + device.deviceSerial + " .progress-bar").css("width", "0%").text("0%");
    $( "#textarea" + device.deviceSerial).val("");
}

function mainNavbarEventHandler(){

    $(".mainNav").on('click', function (e) {

        $(this).parent().parent().find('.active').removeClass('active');
        $('.nav').find('.active').removeClass('active');
        $(this).parent().addClass('active');

        e.preventDefault();
        //e.stopPropagation();

        $('.content').hide();
        var hash = $($(this))

        if (hash.attr("href") === "#jobs") {

            var rows = $('#devices tbody').children().length;

            if (rows > 0) {
                $('#devices tbody > tr').remove();
            }
            loadDeviceTableData();

        } else if (hash.attr("href") === "#config-devices") {

            var rows = $('#tableDeviceConfigs tbody').children().length;

            if (rows > 0) {
                $('#deviceConfigTablePager').empty();
                $('#tableDeviceConfigs tbody > tr').remove();
            }
            loadDeviceConfigTableData();

        } else if (hash.attr("href") === "#config-sites") {

            var rows = $('#tableSites tbody').children().length;

            if (rows > 0) {
                $('#siteTablePager').empty();
                $('#tableSites tbody > tr').remove();
            }
            loadSiteTableData();

        } else if (hash.attr("href") === "#config-groups") {

            var rows = $('#tableGroups tbody').children().length;

            if (rows > 0) {

                $('#groupTablePager').empty();
                $('#tableGroups tbody > tr').remove();
            }
            loadGroupTableData();

        } else if (hash.attr("href") === "#config-templates") {

            var rows = $('#tableTemplates tbody').children().length;

            if (rows > 0) {
                $('#templateTablePager').empty();
                $('#tableTemplates tbody > tr').remove();
            }
            loadTemplateTableData();

        } else if (hash.attr("href") === "#config-images") {

            var rows = $('#tableImages tbody').children().length;

            if (rows > 0) {
                $('#imageTablePager').empty();
                $('#tableImages tbody > tr').remove();
            }
            loadImageTableData();

        } else if (hash.attr("href") === "#config-services") {

            var rows = $('#tableServices tbody').children().length;

            if (rows > 0) {
                $('#tableServices tbody > tr').remove();
            }
            loadServiceTableData();

        } else if (hash.attr("href") === "#log-overview") {
            loadLogViewerData();

        }
        $($(this).attr('href')).show();
    });
}

function initialize(){

    //add modal
    createDeviceConfigAddModal();
    createGroupConfigAddModal();
    createTemplateConfigAddModal();
    createImageConfigAddModal();
    createSiteConfigAddModal();

    //add event handler
    mainNavbarEventHandler();
    deviceConfigSaveBtnEventHandler();
    deviceConfigDelBtnEventHandler();
    deviceAddNewBtnEventHandler();
    groupConfigSaveBtnEventHandler();
    groupConfigDelBtnEventHandler();
    groupAddNewBtnEventHandler();
    templateConfigSaveBtnEventHandler();
    templateConfigDelBtnEventHandler();
    templateAddNewBtnEventHandler();
    imageConfigSaveBtnEventHandler();
    imageConfigDelBtnEventHandler();
    siteConfigSaveBtnEventHandler();
    siteConfigDelBtnEventHandler();
}

function loadLogViewerData() {

    function fetch() {
        $.ajax({
            url: '/api/logs',
            type: 'GET',
            success: function (response) {
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}



function initLogViewerData(data) {
    $("textarea#mainlogviewer").val(data);
}

function appendLogViewerData(data) {
    var box = $("#mainlogviewer");
    box.val(box.val() + data + '\n');
    $("#mainlogviewer").scrollTop($("#mainlogviewer")[0].scrollHeight);
}

$(document).ready(function() {

    var wsurl = scheme + "://" + host + ":" + port + "/yapt/ws?clientname=" + clientname;
    //console.log(wsurl);

    if (window.WebSocket) {
        ws = new WebSocket(wsurl, "yapt");
        initialize();
      }
      else if (window.MozWebSocket) {
        ws = MozWebSocket(wsurl);
        initialize();
      }
      else {
        console.log('WebSocket Not Supported');
        return;
      }

    var $message = $('#message');

    ws.onopen = function(){

      $message.attr("class", 'label label-success');
      $message.text('open');

    };

    ws.onmessage = function(ev){

        var json = JSON.parse(ev.data);
        var ws;

        //console.log(json.deviceTaskProgress);
        //console.log(json.action);
        //console.log(json);

        if(json.action === action_add_device) {
            prepend_device_in_table(json);

        } else if(json.action === action_update_device) {
            update_device_in_table(json);

        } else if (json.action === action_update_device_task_state) {
            update_device_task_state_in_table(json)

        } else if (json.action === action_update_device_and_reset_task_state) {
            update_dev_and_reset_task_state(json);

        } else if (json.action === action_update_status) {
            updateStatus(json);

        } else if (json.action === action_update_log_viewer) {
            appendLogViewerData(json.data);

        } else if (json.action === action_init_log_viewer) {
            initLogViewerData(json.data);

        } else {
            return;
        }
    };

    ws.onclose = function(ev){

      $message.attr("class", 'label label-important');
      $message.text('closed');
    };

    ws.onerror = function(ev){

      $message.attr("class", 'label label-warning');
      $message.text('error occurred');
    };
});

