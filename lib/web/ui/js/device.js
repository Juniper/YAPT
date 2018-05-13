/*
DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
Copyright (c) 2018 Juniper Networks, Inc.
All rights reserved.
Use is subject to license terms.

Author: cklewar
*/

function deviceAddNewBtnEventHandler(){

    $("#deviceConfigAddBtn").on( "click", function() {
        loadStorage($("#comboBoxDeviceCfgStorage"));
        $("#modalDeviceConfigAddNew").modal("show");
    });
}

function deviceConfigLoadCfgBtnEventHandler(device){
    $( "#modal" + device.deviceSerial).on( "click", function() {
        var modal = $('#modal' + device.deviceSerial);
        modal.find('.modal-title').text("Device Name: " + device.deviceName + " ---- Device Serial: " + device.deviceSerial);
        $( "#textarea" + device.deviceSerial).val(device.deviceConfiguration);
    });
}

function deviceConfigSaveBtnEventHandler(){
    $("#deviceConfigSaveBtn").on( "click", function() {
        var formData = new FormData();

        formData.append('name', $("#inputDeviceConfigSerial").val());
        formData.append('descr', $("#inputDeviceConfigDescr").val());
        formData.append('type', 'device');
        formData.append('storage', $("#comboBoxDeviceCfgStorage option:selected").text());
        formData.append('obj', $("#inputDeviceConfigDataFile")[0].files[0]);
        formData.append('objSize', $("#inputDeviceConfigDataFile")[0].files[0].size);

        function upload() {
            $.ajax({
                url: '/api/upload',
                type: 'POST',
                data: formData,
                cache: false,
                contentType: false,
                processData: false,
                success: function (response) {

                    var obj = JSON.parse(response);

                    if (obj[0]) {
                        var rows = $('#tableDeviceConfigs tbody').children().length;

                        if (rows > 0) {
                            $('#tableDeviceConfigs tbody > tr').remove();
                        }
                        $('#deviceConfigTablePager').empty();
                        loadDeviceConfigTableData();
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_SUCCESS,
                            title: 'Successfully added new device',
                            message: obj[1]
                        });
                    } else {
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new device',
                            message: obj[1]
                        });
                    }
                },
                error : function (data, errorText) {
                    $("#errormsg").html(errorText).show();
                }
            });
        }

        if ($("#inputDeviceConfigSerial").val() && $("#inputDeviceConfigDataFile").val()) {
            upload();
            $("#inputDeviceConfigDataFile").val("");
        } else {
            if (!$("#inputDeviceConfigSerial").val()){
                BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new device',
                            message: "Empty device name not allowed"
                        });
            } else if (!$("#inputDeviceConfigDataFile").val()) {
                BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new device',
                            message: "No file chosen"
                        });
            }
        }
    });
}

function deviceConfigDelBtnEventHandler() {
    $("#deviceConfigDelBtn").on( "click", function() {

        function del(configSerial, configSource) {
                $.ajax({
                    url: '/api/device?action=del&name=' + configSerial + '&storage=' + configSource,
                    type: 'POST',
                    cache: false,
                    contentType: false,
                    processData: false,
                    success: function (response) {

                        var obj = JSON.parse(response);

                        if (obj[0]) {
                            var rows = $('#tableDeviceConfigs tbody').children().length;

                            if (rows > 0) {
                                $('#tableDeviceConfigs tbody > tr').remove();
                            }

                            $('#deviceConfigTablePager').empty();
                            loadDeviceConfigTableData();
                            BootstrapDialog.show({
                                type: BootstrapDialog.TYPE_SUCCESS,
                                title: 'Successfully deleted device configuration',
                                message: obj[1]
                            });
                        } else {
                            BootstrapDialog.show({
                                type: BootstrapDialog.TYPE_WARNING,
                                title: 'Error deleting device configuration',
                                message: obj[1]
                            });
                        }
                    },
                    error : function (data, errorText) {
                        $("#errormsg").html(errorText).show();
                    }
                });
            }

        var selectedRows = $('#tableDeviceConfigs').find('tbody').find('tr').has('input[type=checkbox]:checked')

        if (selectedRows) {
            $( selectedRows ).each( function( index, element ){
                del($(this).find('td').eq(1).text(), $(this).find('td').eq(3).text());
            });
        }
    });
}

function deviceConfigCloseBtnEventHandler(configSerial){

    $("#deviceCfgCloseBtn" + configSerial).on( "click", function() {
        $("#modalDeviceCfg" + configSerial).remove();
        $('.modal-backdrop').remove();
    });
}

function createDeviceConfigTable(configs){
    var trHTML = '';

        $.each(configs, function (i, config) {
            trHTML +=
            "<tr id=configId-" + config['configId'] + ">" +
                "<td>" +
                "<input type=\"checkbox\" class=\"filled-in\" id=\"checkbox-" + config['configId'] + "\">" +
                "<label for=\"checkbox-" + config['configId'] + "\"class=\"label-table\"></label>" +
                "</td>" +
                "<td>" + config['configSerial'] + "</td>" +
                "<td>" + config['configDescr'] + "</td>" +
                "<td>" + config['configConfigSource'] + "</td>" +
                "<td>" +
                    "<button id=\"configCfg" + config['configSerial'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-eye-open\"></button>" +
                "</td>"
            "</tr>"
        });
        $('#tableDeviceConfigs').append(trHTML);

        $.each(configs, function (i, config) {
            $('#configCfg' + config['configSerial']).on("click", function(){
                    createDeviceConfigModal(config['configSerial']);
                    deviceConfigCloseBtnEventHandler(config['configSerial']);
                    loadDeviceConfiguration(config['configSerial']);
                    $("#modalDeviceCfg" + config['configSerial']).modal("show");
                });
        });
        $('#tableDeviceConfigs tbody').pageTable({pagerSelector:'#deviceConfigTablePager',showPrevNext:true,hidePageNumbers:false,perPage:10});
}

function createDeviceConfigModal(configSerial){

    var deviceConfigModal = "<div class=\"modal fade\" id=\"modalDeviceCfg" + configSerial + "\" role=\"dialog\">" +
    "<div class=\"modal-dialog modal-lg\">" +
      //<!-- Modal content-->
      "<div class=\"modal-content\">" +
        "<div class=\"modal-header\">" +
          "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
          "<h4 class=\"modal-title\">Device Configuration</h4>" +
        "</div>" +
        "<div class=\"modal-body\">" +
            "<div id=\"textarea-wrapper\">" +
                "<textarea id=\"textarea" + configSerial + "\" readonly rows=\"20\" style=\"min-width: 100%\">No data available</textarea>" +
             "</div>" +
        "</div>" +
        "<div class=\"modal-footer\">" +
          "<button type=\"button\" class=\"btn btn-default\" id=\"deviceCfgCloseBtn" + configSerial + "\">Close</button>"
        "</div>" +
      "</div>" +
    "</div>" +
    "</div>";
    $('body').append(deviceConfigModal);
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

function createDeviceConfigAddModal(){

    var createDeviceConfigAddModal = "<div class=\"modal fade\" id=\"modalDeviceConfigAddNew\" role=\"dialog\">" +
        "<div class=\"modal-dialog modal-lg\">" +
          //<!-- Modal content-->
          "<div class=\"modal-content\">" +
            "<div class=\"modal-header\">" +
              "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
              "<h4 class=\"modal-title\">Add new device configuration</h4>" +
            "</div>" +
            "<div class=\"modal-body\">" +
                "<form class=\"form-horizontal\" id=\"formDeviceFileUpload\">" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputDeviceConfigSerial\" class=\"col-sm-3 control-label\">Configuration Serial</label>" +
                    "<div class=\"col-sm-6\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputDeviceConfigSerial\" placeholder=\"New Configuration Serial\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputDeviceConfigDescr\" class=\"col-sm-3 control-label\">Configuration Description</label>" +
                    "<div class=\"col-sm-6\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputDeviceConfigDescr\" placeholder=\"Configuration Description\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"comboBoxDeviceCfgStorage\" class=\"col-sm-3 control-label\">Storage</label>" +
                    "<div class=\"col-sm-4\">" +
                        "<select id=\"comboBoxDeviceCfgStorage\" class=\"form-control comboBoxStorage\" name=\"comboBoxDeviceCfgStorage\">" +
                            "<option value=\"\">Choose storage type</option>" +
                        "</select>" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputDeviceConfigDataFile\" class=\"col-sm-3 control-label\">Configuration Data File</label>" +
                    "<div class=\"col-sm-4\">" +
                      "<input type=\"file\" name=\"obj\" id=\"inputDeviceConfigDataFile\" placeholder=\"Configuration Data File\" accept=\".yml\">" +
                    "</div>" +
                  "</div>" +
                "</form>" +
            "</div>" +
            "<div class=\"modal-footer\">" +
              "<button type=\"button\" class=\"btn btn-default\" id=\"deviceConfigSaveBtn\">Save</button>" +
              "<button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Close</button>" +
            "</div>" +
          "</div>" +
        "</div>" +
    "</div>";
  $('body').append(createDeviceConfigAddModal);
}

function loadDeviceTableData() {

    function fetch() {
        $.ajax({
            url: '/api/device?action=all',
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

function loadDeviceConfigTableData() {

    function fetch() {
        $.ajax({
            url: '/api/device',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=cfgall',
            success: function (response) {

                if (response[0]) {
                    createDeviceConfigTable(response[1]);
                } else {
                    BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error getting device configuration information',
                            message: response[1]
                    });
                }
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}

function loadDeviceConfiguration(configSerial) {

    function fetch() {
        $.ajax({
            url: '/api/device',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=config&name=' + configSerial,
            success: function (response) {
                $("#textarea" + configSerial).val(response[1]);
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}