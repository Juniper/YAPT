function makeProgress(device){
    //console.log(device.taskProgress, device.taskKey, device.taskKeyState);
    $("#" + device.deviceSerial + " .progress-bar").css("width", device.taskProgress + "%").text(device.taskProgress + "%");
}

function addEventHandler(device){
    $( "#modal" + device.deviceSerial).on( "click", function() {
        var modal = $('#modal' + device.deviceSerial);
        modal.find('.modal-title').text("Device Name: " + device.deviceName + " ---- Device Serial: " + device.deviceSerial);
        $( "#textarea" + device.deviceSerial).val(device.deviceConfiguration);

    });
}

function prepend_device_in_table(device){

    var newTaskStatusRow = "";
    device.deviceTasksStates.forEach(function (value, i) {
        tempRow = "<tr id=" + device.deviceTaskSequence[i] + "><td>" + device.deviceTaskSequence[i] + "</td>" + "<td colspan=\"3\">" + value[1] + "</td></tr>";
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
                            "<div class=\"progress-bar progress-bar-custom\" role=\"progressbar\" aria-valuenow=\"" + device.taskProgress + "\" aria-valuemin=\"0\" aria-valuemax=\"100\" style=\"width:" + device.taskProgress + "%\">" +
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
                                        "<td>Configuration: " +
                                        "<button id=\"configDetail" + device.deviceSerial + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-eye-open\" data-toggle=\"modal\" data-target=\"#modal" + device.deviceSerial + "\"></button>" +
                                        "</td>" +
                                        "<td>Connection: " + device.deviceConnection + "</td>" +
                                        "<td>Source Plugin: " + device.deviceSourcePlugin + "</td>" +
                                        "<td>Group: " + device.deviceGroup + "</td>" +
                                    "</tr>" +
                                    "<tr>" +
                                    "<th>Task</th>" + "<th colspan\"3\">Status</th>" +
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
    addEventHandler(device);
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
}

function update_device_task_state_in_table(device){

        $("#task" + device.deviceSerial + " tbody #" + device.taskName + " td:nth-child(2)").hide();
        $("#task" + device.deviceSerial + " tbody #" + device.taskName + " td:nth-child(2)").fadeIn("slow");
        $("#task" + device.deviceSerial + " tbody #" + device.taskName + " td:nth-child(2)").text(device.taskState.taskStateMsg);
        makeProgress(device);
}

function update_dev_and_reset_task_state(device){

    update_device_in_table(device)
    $("#task" + device.deviceSerial + " tbody tr td:nth-child(2)").each(function(i) {
            $(this).text('Waiting');
    });

    $("#" + device.deviceSerial + " .progress-bar").css("width", "0%").text("0%");
    $( "#textarea" + device.deviceSerial).val("");
}

function createDevConfigModal(device){

  var deviceConfigModal = "<div class=\"modal fade\" id=\"modal" + device.deviceSerial + "\" role=\"dialog\">" +
    "<div class=\"modal-dialog modal-lg\">" +
      //<!-- Modal content-->
      "<div class=\"modal-content\">" +
        "<div class=\"modal-header\">" +
          "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
          "<h4 class=\"modal-title\">Device Configuration</h4>" +
        "</div>" +
        "<div class=\"modal-body\">" +
            "<div id=\"textarea-wrapper\">" +
                "<textarea id=\"textarea" + device.deviceSerial + "\" readonly rows=\"20\" style=\"min-width: 100%\">No data available</textarea>" +
             "</div>" +
        "</div>" +
        "<div class=\"modal-footer\">" +
          "<button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Close</button>"
        "</div>" +
      "</div>" +
    "</div>" +
  "</div>";

  $("#textarea" + device.deviceSerial).val(device.deviceConfiguration);
  $('body').append(deviceConfigModal);
}

function createGroupConfigModal(groupName){

  var groupConfigModal = "<div class=\"modal fade\" id=\"modal" + groupName + "\" role=\"dialog\">" +
    "<div class=\"modal-dialog modal-lg\">" +
      //<!-- Modal content-->
      "<div class=\"modal-content\">" +
        "<div class=\"modal-header\">" +
          "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
          "<h4 class=\"modal-title\">Group Configuration</h4>" +
        "</div>" +
        "<div class=\"modal-body\">" +
          "<div id=\"textarea-wrapper\">" +
            "<textarea id=\"textarea" + groupName + "\" class=\"vertical\" readonly rows=\"20\" style=\"min-width: 100%\">No data available</textarea>" +
          "</div>" +
        "</div>" +
        "<div class=\"modal-footer\">" +
          "<button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Close</button>"
        "</div>" +
      "</div>" +
    "</div>" +
  "</div";

  loadGroupConfiguration(groupName);
  $('body').append(groupConfigModal);
}

function initialize(){

    $(".mainNav").on('click', function (e) {

        $(this).parent().parent().find('.active').removeClass('active');
        $('.nav').find('.active').removeClass('active');
        $(this).parent().addClass('active');

        e.preventDefault();
        $('.content').hide();
        var hash = $($(this))

        if (hash.attr("href") === "#jobs") {

            var rows = $('#devices tbody').children().length;

            if (rows > 0) {
                $('#devices tbody > tr').remove();
            }
            loadDeviceTableData();

        } else if (hash.attr("href") === "#config-sites") {

            var rows = $('#tableSites tbody').children().length;

            if (rows > 0) {
                $('#tableSites tbody > tr').remove();
            }
            loadSiteTableData();

        } else if (hash.attr("href") === "#config-groups") {

            var rows = $('#tableGroups tbody').children().length;

            if (rows > 0) {
                $('#tableGroups tbody > tr').remove();
            }
            loadGroupTableData();

        } else if (hash.attr("href") === "#log-overview") {
            loadLogViewerData();

        }

        $($(this).attr('href')).show();
    });
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

function loadSiteTableData() {

    function fetch() {
        $.ajax({
            url: '/api/site',
            dataType: 'json',
            data: 'siteId=all',
            success: function (response) {
                var trHTML = '';

                $.each(response, function (i, site) {
                    trHTML +=
                    "<tr id=siteId-" + site['siteId'] + ">" +
                        "<td>" +
                            "<button class=\"btn btn-default btn-xs\" data-toggle=\"collapse\" data-target=\"#data-" + site['siteId'] + "\" class=\"accordion-toggle\">" +
                                "<span class=\"glyphicon glyphicon-tasks\"></span>" +
                            "</button>" +
                        "</td>" +
                        "<td>" + site['siteId'] + "</td>" +
                        "<td>" + site['siteName'] + "</td>" +
                        "<td>" + site['siteDescr'] + "</td>" +
                    "</tr>" +
                    "<tr>" +
                    "<td colspan=\"9\" class=\"hiddenRow\">" +
                        "<div class=\"accordian-body collapse\" id=\"data-" + site['siteId'] + "\">" +
                            "<table class=\"table table-hover\" id=\"asset-" + site['siteId'] + "\">" +
                                "<thead>" +
                                    "<th>Asset Serial</th><th>Asset Config ID</th><th>Asset Description</th>" +
                                    "</tr>" +
                                "</thead>"
                                "<tbody>";

                    $.each(site['assets'], function (i, asset) {
                        //assetID missing from backend
                        trHTML +=
                        "<tr id=" + asset['assetId'] + "><td>" + asset['assetSerial'] + "</td>" + "<td>" + asset['assetConfigId'] + "</td><td>" + asset['assetDescr'] + "</td></tr>";
                    });

                    trHTML += "</tbody>" +
                            "</table>" +
                        "</div>" +
                    "</td>" +
                "</tr>";
                });
                $('#tableSites').append(trHTML);
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}

function loadGroupTableData() {

    function fetch() {
        $.ajax({
            url: '/api/group',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=all',
            success: function (response) {
                var trHTML = '';

                $.each(response, function (i, group) {
                    trHTML +=
                    "<tr id=groupId-" + group['siteId'] + ">" +
                        "<td>" + group['groupId'] + "</td>" +
                        "<td>" + group['groupName'] + "</td>" +
                        "<td>" + group['groupDescr'] + "</td>" +
                        "<td>" +
                            "<button id=\"configDetail" + group['groupName'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-eye-open\" data-toggle=\"modal\" data-target=\"#modal" + group['groupName'] + "\"></button>" +
                        "</td>"
                    "</tr>"
                    createGroupConfigModal(group['groupName']);
                });
                $('#tableGroups').append(trHTML);

            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}

function loadGroupConfiguration(groupName) {

    function fetch() {
        $.ajax({
            url: '/api/group',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=config&name=' + groupName,
            success: function (response) {
                $("#textarea" + groupName).val(response);
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}

function loadDeviceTableData() {

    function fetch() {
        $.ajax({
            url: '/api/device?sn=all',
            dataType: 'json',
            success: function (response) {
                $.each(response, function (i, device) {
                    prepend_device_in_table(device);
                });
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

