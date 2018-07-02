/*
DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
Copyright (c) 2018 Juniper Networks, Inc.
All rights reserved.
Use is subject to license terms.

Author: cklewar
*/

function templateAddNewBtnEventHandler(){
    $("#templateAddBtn").on( "click", function() {

        loadGroups($("#comboBoxTemplateDevGroup"));
        loadStorage($("#comboBoxTemplateStorage"));
        $("#modalTemplateAddNew").modal("show");
    });
}

function templateConfigSaveBtnEventHandler(){
    $("#templateSaveBtn").on( "click", function() {

        var formData = new FormData();

        formData.append('name', $("#inputTemplateName").val());
        formData.append('descr', $("#inputTemplateDescr").val());
        formData.append('type', 'template');
        formData.append('group', $("#comboBoxTemplateDevGroup option:selected").text());
        formData.append('storage', $("#comboBoxTemplateStorage option:selected").text());
        formData.append('obj', $("#inputTemplateDataFile")[0].files[0]);
        formData.append('objSize', $("#inputTemplateDataFile")[0].files[0].size);

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
                        var rows = $('#tableTemplates tbody').children().length;

                        if (rows > 0) {
                            $('#tableTemplates tbody > tr').remove();
                        }

                        $('#templateTablePager').empty();
                        loadTemplateTableData();
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_SUCCESS,
                            title: 'Successfully added new template',
                            message: obj[1]
                        });
                    } else {
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new template',
                            message: obj[1]
                        });
                    }
                },
                error : function (data, errorText) {
                    $("#errormsg").html(errorText).show();
                }
            });
        }

        if ($("#inputTemplateName").val() && $("#inputTemplateDataFile").val()) {
            upload();
            $("#inputTemplateDataFile").val("");
        } else {
            if (!$("#inputTemplateName").val()){
                BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new template',
                            message: "Empty template name not allowed"
                });

            } else if (!$("#inputTemplateDataFile").val()) {
                BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new template',
                            message: "No file chosen"
                });
            }
        }
    });
}

function templateConfigDelBtnEventHandler() {
    $("#templateDelBtn").on( "click", function() {

        function del(templateName) {
                $.ajax({
                    url: '/api/template?action=del&name=' + templateName,
                    type: 'POST',
                    cache: false,
                    contentType: false,
                    processData: false,
                    success: function (response) {

                        var obj = JSON.parse(response);

                        if (obj[0]) {
                            var rows = $('#tableTemplates tbody').children().length;

                            if (rows > 0) {
                                $('#tableTemplates tbody > tr').remove();
                            }

                            $('#tempalteTablePager').empty();
                            loadTemplateTableData();
                            BootstrapDialog.show({
                                type: BootstrapDialog.TYPE_SUCCESS,
                                title: 'Successfully deleted template',
                                message: obj[1]
                            });

                        } else {
                            BootstrapDialog.show({
                                type: BootstrapDialog.TYPE_WARNING,
                                title: 'Error deleting template',
                                message: obj[1]
                            });
                        }
                    },
                    error : function (data, errorText) {
                        $("#errormsg").html(errorText).show();
                    }
                });
            }

        var selectedRows = $('#tableTemplates').find('tbody').find('tr').has('input[type=checkbox]:checked')

        if (selectedRows) {
            $( selectedRows ).each( function( index, element ){
                del($(this).find('td').eq(1).text());
            });
        }
    });
}

function templateConfigCloseBtnEventHandler(templateName){

    $("#templateCfgCloseBtn" + templateName).on( "click", function() {
        $("#modalTemplateCfg" + templateName).remove();
        $('.modal-backdrop').remove();
    });
}

function createTemplateConfigTable(templates){
    var trHTML = '';

        $.each(templates, function (i, template) {
            trHTML +=
            "<tr id=templateId-" + template['templateId'] + ">" +
                "<td>" +
                "<input type=\"checkbox\" class=\"filled-in\" id=\"checkbox-" + template['templateId'] + "\">" +
                "<label for=\"checkbox-" + template['templateId'] + "\"class=\"label-table\"></label>" +
                "</td>" +
                "<td>" + template['templateName'] + "</td>" +
                "<td>" + template['templateDescr'] + "</td>" +
                "<td>" + template['templateConfigSource'] + "</td>" +
                "<td>" +
                    "<button id=\"templateCfg" + template['templateName'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-eye-open\" data-toggle=\"modal\" data-target=\"#modal" + template['templateName'] + "\"></button>" +
                "</td>"
            "</tr>"
        });
        $('#tableTemplates').append(trHTML);

        $.each(templates, function (i, template) {
            $('#templateCfg' + template['templateName']).on("click", function(){
                    createTemplateConfigModal(template['templateName']);
                    templateConfigCloseBtnEventHandler(template['templateName']);
                    loadTemplateConfiguration(template['templateName']);
                    $("#modalTemplateCfg" + template['templateName']).modal("show");
                });
        });
        $('#tableTemplates tbody').pageTable({pagerSelector:'#templateTablePager',showPrevNext:true,hidePageNumbers:false,perPage:10});
}

function createTemplateConfigModal(templateName){

  var templateConfigModal = "<div class=\"modal fade\" id=\"modalTemplateCfg" + templateName + "\" role=\"dialog\">" +
    "<div class=\"modal-dialog modal-lg\">" +
      //<!-- Modal content-->
      "<div class=\"modal-content\">" +
        "<div class=\"modal-header\">" +
          "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
          "<h4 class=\"modal-title\">Template Configuration</h4>" +
        "</div>" +
        "<div class=\"modal-body\">" +
          "<div id=\"textarea-wrapper\">" +
            "<textarea id=\"textarea" + templateName + "\" class=\"vertical\" readonly rows=\"20\" style=\"min-width: 100%\">No data available</textarea>" +
          "</div>" +
        "</div>" +
        "<div class=\"modal-footer\">" +
          "<button type=\"button\" class=\"btn btn-default\" id=\"templateCfgCloseBtn" + templateName + "\">Close</button>"
        "</div>" +
      "</div>" +
    "</div>" +
  "</div";
  $('body').append(templateConfigModal);
}

function createTemplateConfigAddModal(){

    var createTemplateConfigAddModal = "<div class=\"modal fade\" id=\"modalTemplateAddNew\" role=\"dialog\">" +
        "<div class=\"modal-dialog modal-lg\">" +
          //<!-- Modal content-->
          "<div class=\"modal-content\">" +
            "<div class=\"modal-header\">" +
              "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
              "<h4 class=\"modal-title\">Add new template configuration</h4>" +
            "</div>" +
            "<div class=\"modal-body\">" +
                "<form class=\"form-horizontal\" id=\"formTemplateFileUpload\">" +
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
                "</form>" +
            "</div>" +
            "<div class=\"modal-footer\">" +
              "<button type=\"button\" class=\"btn btn-default\" id=\"templateSaveBtn\">Save</button>" +
              "<button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Close</button>" +
            "</div>" +
          "</div>" +
        "</div>" +
    "</div>";
  $('body').append(createTemplateConfigAddModal);
}

function loadTemplateTableData() {

    function fetch() {
        $.ajax({
            url: '/api/template',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=all',
            success: function (response) {

                if (response[0]) {
                    createTemplateConfigTable(response[1]);
                } else {
                    BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error getting template information',
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

function loadTemplateConfiguration(templateName) {

    function fetch() {
        $.ajax({
            url: '/api/template',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=config&name=' + templateName,
            success: function (response) {
                $("#textarea" + templateName).val(response[1]);
            },
            error : function (data, errorText) {
                $("#errormsg").html(errorText).show();
            }
        });
    }
    fetch();
}