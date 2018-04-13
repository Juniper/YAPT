/*
DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
Copyright (c) 2018 Juniper Networks, Inc.
All rights reserved.
Use is subject to license terms.
*/

function serviceConfigCloseBtnEventHandler(serviceName){

    $("#serviceCfgCloseBtn" + serviceName).on( "click", function() {
        $("#modalServiceCfg" + serviceName).remove();
        $('.modal-backdrop').remove();
    });
}

function createServiceConfigTable(services){
    var trHTML = '';

        $.each(services, function (i, service) {

            trHTML +=
            "<tr id=serviceId-" + service['serviceId'] + ">" +
                "<td>" +
                "<input type=\"checkbox\" class=\"filled-in\" id=\"checkbox-" + service['serviceId'] + "\">" +
                "<label for=\"checkbox-" + service['serviceId'] + "\"class=\"label-table\"></label>" +
                "</td>" +
                "<td>" + service['serviceName'] + "</td>" +
                "<td>" + service['serviceDescr'] + "</td>" +
                "<td>" + service['serviceStatus'] + "</td>" +
                "<td>" +
                    "<button id=\"serviceCfgBtn" + service['serviceName'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-eye-open\" data-target=\"#modalServiceMod" + service['serviceName'] + "\"></button>" +
                    "<button id=\"serviceModBtn" + service['serviceName'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-edit\" data-toggle=\"modal\" data-target=\"#modalServiceMod" + service['serviceName'] + "\"></button>" +
                    "<button id=\"serviceStartBtn" + service['serviceName'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-play\" data-toggle=\"modal\" data-target=\"#modalServiceStart" + service['serviceName'] + "\"></button>" +
                    "<button id=\"serviceStopBtn" + service['serviceName'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-stop\" data-toggle=\"modal\" data-target=\"#modalServiceStop" + service['serviceName'] + "\"></button>" +
                    "<button id=\"serviceRestartBtn" + service['serviceName'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-refresh\" data-toggle=\"modal\" data-target=\"#modalServicRestart" + service['serviceName'] + "\"></button>" +
                "</td>"
            "</tr>"
        });
        $('#tableServices').append(trHTML);

        $.each(services, function (i, service) {
            $('#serviceCfgBtn' + service['serviceName']).on("click", function(){
                    createServiceConfigModal(service['serviceName']);
                    serviceConfigCloseBtnEventHandler(service['serviceName']);
                    loadServiceConfiguration(service['serviceName']);
                    $("#modalServiceCfg" + service['serviceName']).modal("show");
            });
            $('#serviceModBtn' + service['serviceName']).on("click", function(){
                    createServiceConfigModal(service['serviceName']);
                    serviceConfigCloseBtnEventHandler(service['serviceName']);
                    loadServiceConfiguration(service['serviceName']);
                    $("#modalServiceCfg" + service['serviceName']).modal("show");
            });
            $('#serviceStartBtn' + service['serviceName']).on("click", function(){
                    //createServiceConfigModal(service['serviceName']);
                    //serviceConfigCloseBtnEventHandler(service['serviceName']);
                    //loadServiceConfiguration(service['serviceName']);
                    //$("#modalServiceCfg" + service['serviceName']).modal("show");
                    startService(service['serviceName']);
            });
            $('#serviceStopBtn' + service['serviceName']).on("click", function(){
                    //createServiceConfigModal(service['serviceName']);
                    //serviceConfigCloseBtnEventHandler(service['serviceName']);
                    //loadServiceConfiguration(service['serviceName']);
                    //$("#modalServiceCfg" + service['serviceName']).modal("show");
                    stopService(service['serviceName']);
            });
            $('#serviceRestartBtn' + service['serviceName']).on("click", function(){
                    createServiceConfigModal(service['serviceName']);
                    serviceConfigCloseBtnEventHandler(service['serviceName']);
                    loadServiceConfiguration(service['serviceName']);
                    $("#modalServiceCfg" + service['serviceName']).modal("show");
            });
        });
}

function createServiceConfigModal(serviceName){

    var serviceConfigModal = "<div class=\"modal fade\" id=\"modalServiceCfg" + serviceName + "\" role=\"dialog\">" +
    "<div class=\"modal-dialog modal-lg\">" +
      //<!-- Modal content-->
      "<div class=\"modal-content\">" +
        "<div class=\"modal-header\">" +
          "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
          "<h4 class=\"modal-title\">Service Configuration</h4>" +
        "</div>" +
        "<div class=\"modal-body\">" +
          "<div id=\"textarea-wrapper\">" +
            "<textarea id=\"textarea" + serviceName + "\" class=\"vertical\" readonly rows=\"20\" style=\"min-width: 100%\">No data available</textarea>" +
          "</div>" +
        "</div>" +
        "<div class=\"modal-footer\">" +
          "<button type=\"button\" class=\"btn btn-default\" id=\"serviceCfgCloseBtn" + serviceName + "\">Close</button>"
        "</div>" +
      "</div>" +
    "</div>" +
  "</div";
  $('body').append(serviceConfigModal);
}

function loadServiceTableData() {

    function fetch() {
        $.ajax({
            url: '/api/service',
            type: 'GET',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=all',
            success: function (response) {
                console.log(response);
                console.log(response[0]);
                console.log(response[1]);

                if (response[0]) {
                    createServiceConfigTable(response[1]);
                } else {
                    BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error getting service information',
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

function loadServiceConfiguration(serviceName) {

    function fetch() {
        $.ajax({
            url: '/api/service',
            type: 'GET',
            dataType: 'text',
            contentType: 'application/json',
            data: 'action=config&name=' + serviceName,
            success: function (response) {
                $("#textarea" + serviceName).val(response);
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}

function modServiceConfiguration(serviceName){
    function fetch() {
        $.ajax({
            url: '/api/service',
            type: 'GET',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=config&name=' + serviceName,
            success: function (response) {

                console.log(response);
                console.log(response.Name);
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}

function startService(serviceName){
    console.log('start service');

    function fetch() {
        $.ajax({
            url: '/api/service?action=start&name=' + serviceName,
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            //data: 'action=start&name=' + serviceName,
            processData: true,
            //contentType: false,
            success: function (response) {

                console.log(response);
            },
            error : function (data, errorText) {
                console.log(data);
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}

function stopService(serviceName){
    console.log('stop service');

    function fetch() {
        $.ajax({
            url: '/api/service?action=stop&name=' + serviceName,
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            //data: 'action=stop&name=' + serviceName,
            success: function (response) {

                console.log(response);
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}

function restartService(serviceName){
}