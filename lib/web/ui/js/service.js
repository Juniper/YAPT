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

function serviceModConfigCloseBtnEventHandler(serviceName){

    $("#serviceModCfgCloseBtn" + serviceName).on( "click", function() {
        $("#modalServiceModCfg" + serviceName).remove();
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
                "<td id=t_svc_status-" + service['serviceName'] + " class=\"col-md-2\">" + service['serviceStatus'] + "</td>" +
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
                    console.log(loadServiceConfiguration(service['serviceName']));
                    loadServiceConfiguration(service['serviceName']);
                    $("#modalServiceCfg" + service['serviceName']).modal("show");
            });
            $('#serviceModBtn' + service['serviceName']).on("click", function(){
                    createServiceConfigModModal(service['serviceName']);
                    serviceModConfigCloseBtnEventHandler(service['serviceName']);
                    loadServiceConfigurationElements(service['serviceName']);
                    $("#modalServiceModCfg" + service['serviceName']).modal("show");
            });
            $('#serviceStartBtn' + service['serviceName']).on("click", function(){
                    startService(service['serviceName']);
            });
            $('#serviceStopBtn' + service['serviceName']).on("click", function(){
                    stopService(service['serviceName']);
            });
            $('#serviceRestartBtn' + service['serviceName']).on("click", function(){
                    restartService(service['serviceName']);
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

function createServiceConfigModModal(serviceName){

    var createServiceConfigModModal = "<div class=\"modal fade\" id=\"modalServiceModCfg" + serviceName + "\" role=\"dialog\">" +
        "<div class=\"modal-dialog modal-lg\">" +
          //<!-- Modal content-->
          "<div class=\"modal-content\">" +
            "<div class=\"modal-header\">" +
              "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
              "<h4 class=\"modal-title\">Modify " + serviceName + " service configuration</h4>" +
            "</div>" +
            "<div id=\"modalBodyModCfg" + serviceName + "\" class=\"modal-body\">" +
            "</div>" +
            "<div class=\"modal-footer\">" +
              "<button type=\"button\" class=\"btn btn-default\" id=\"serviceModBtn\">Save</button>" +
              "<button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Close</button>" +
            "</div>" +
          "</div>" +
        "</div>" +
    "</div>";
  $('body').append(createServiceConfigModModal);
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
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=config&name=' + serviceName,
            success: function (response) {

                cfg = jQuery.parseJSON(response);

                if (cfg[0]){
                    $("#textarea" + serviceName).val(cfg[1]);
                } else {
                    console.log('Error in getting service configuration');
                }
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}

function loadServiceConfigurationElements(serviceName){

    console.log('inside');

    function fetch() {
        $.ajax({
            url: '/api/service',
            type: 'GET',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=json&name=' + serviceName,
            success: function (response) {

                data = jQuery.parseJSON(response);

                if (data[0]){

                    cfg = jQuery.parseJSON(data[1]);
                    modalBody = "<form class=\"form-horizontal\" id=\"formModService\">";
                    //console.log(cfg);
                    //console.log(typeof(cfg));
                    $.each(cfg, function(i, item) {
                        //console.log(i, item);
                        //console.log(typeof(item));
                        if (typeof(item) === 'object') {
                            console.log(i, item);
                            $.each(item, function(j, subitem) {
                                console.log(j, subitem);
                                modalBody = modalBody + "<div class=\"form-group\">" +
                                "<label for=\"input" + i + j +"\" class=\"col-sm-3 control-label\">" + i + ' ' + j + "</label>" +
                                "<div class=\"col-sm-6\">" +
                                    "<input type=\"text\" class=\"form-control\" id=\"input" + i + j + "\" placeholder=\""+ i + ' ' + j +"\" value=\"" + subitem + "\">" +
                                "</div>" +
                            "</div>";

                            });
                        } else {
                            modalBody = modalBody + "<div class=\"form-group\">" +
                                "<label for=\"input" + i +"\" class=\"col-sm-3 control-label\">" + i + "</label>" +
                                "<div class=\"col-sm-6\">" +
                                    "<input type=\"text\" class=\"form-control\" id=\"input" + i + "\" placeholder=\"" + item + "\" value=\"" + item + "\">" +
                                "</div>" +
                            "</div>";
                        }
                    });
                    modalBody = modalBody + "</form>";

                    /*
                    modalBody = "<form class=\"form-horizontal\" id=\"formModService\">" +
                      "<div class=\"form-group\">" +
                        "<label for=\"inputTemplateName\" class=\"col-sm-3 control-label\">Template Name</label>" +
                        "<div class=\"col-sm-6\">" +
                          "<input type=\"text\" class=\"form-control\" id=\"inputTemplateName\" placeholder=\"New Template Name\">" +
                        "</div>" +
                      "</div>" +
                      "<div class=\"form-group\">" +
                        "<label for=\"inputTemplateDescr\" class=\"col-sm-3 control-label\">Template Description</label>" +
                        "<div class=\"col-sm-6\">" +
                          "<input type=\"text\" class=\"form-control\" id=\"inputTemplateDescr\" placeholder=\"Template Description\">" +
                        "</div>" +
                      "</div>" +
                      "<div class=\"form-group\">" +
                        "<label for=\"comboBoxTemplateStorage\" class=\"col-sm-3 control-label\">Storage</label>" +
                        "<div class=\"col-sm-4\">" +
                            "<select id=\"comboBoxTemplateStorage\" class=\"form-control comboBoxStorage\" name=\"comboBoxTemplateStorage\">" +
                                "<option value=\"\">Choose storage type</option>" +
                            "</select>" +
                        "</div>" +
                      "</div>" +
                      "<div class=\"form-group\">" +
                        "<label for=\"comboBoxTemplateDevGroup\" class=\"col-sm-3 control-label\">Device Group</label>" +
                        "<div class=\"col-sm-4\">" +
                            "<select id=\"comboBoxTemplateDevGroup\" class=\"form-control comboBoxDevGroup\" name=\"comboBoxTemplateDevGroup\">" +
                                "<option value=\"\">Choose device group</option>" +
                            "</select>" +
                        "</div>" +
                      "</div>" +
                      "<div class=\"form-group\">" +
                        "<label for=\"inputTemplateDataFile\" class=\"col-sm-3 control-label\">Template Data File</label>" +
                        "<div class=\"col-sm-4\">" +
                          "<input type=\"file\" name=\"obj\" id=\"inputTemplateDataFile\" placeholder=\"Template Data File\" accept=\".j2\">" +
                        "</div>" +
                      "</div>" +
                    "</form>";
                    */
                   if ($("#modalBodyModCfg" + serviceName)){
                    $("#modalBodyModCfg" + serviceName).empty();
                    $("#modalBodyModCfg" + serviceName).append(modalBody);
                   } else {
                    $("#modalBodyModCfg" + serviceName).append(modalBody);
                   }
                } else {
                    console.log('Error in getting service configuration');
                }
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}

function startService(serviceName){

    function fetch() {
        $.ajax({
            url: '/api/service?action=start&name=' + serviceName,
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            processData: true,
            success: function (response) {
                $("#t_svc_status-" + serviceName).html(jQuery.parseJSON(response));
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}

function stopService(serviceName){

    function fetch() {
        $.ajax({
            url: '/api/service?action=stop&name=' + serviceName,
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            success: function (response) {

                $("#t_svc_status-" + serviceName).html(jQuery.parseJSON(response));
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}

function restartService(serviceName){

    function fetch() {
        $.ajax({
            url: '/api/service?action=restart&name=' + serviceName,
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            success: function (response) {

                $("#t_svc_status-" + serviceName).text(jQuery.parseJSON(response));
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}