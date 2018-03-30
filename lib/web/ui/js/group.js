/*
DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
Copyright (c) 2018 Juniper Networks, Inc.
All rights reserved.
Use is subject to license terms.
*/

function groupAddNewBtnEventHandler(){
    $("#groupAddBtn").on( "click", function() {

        loadStorage($("#comboBoxGroupStorage"));
        $("#modalGroupAddNew").modal("show");
    });
}

function groupConfigSaveBtnEventHandler(){
    $("#groupSaveBtn").on( "click", function() {

        var formData = new FormData();

        formData.append('name', $("#inputGroupName").val());
        formData.append('descr', $("#inputGroupDescr").val());
        formData.append('type', 'group');
        formData.append('storage', $("#comboBoxGroupStorage option:selected").text());
        formData.append('obj', $("#inputGroupDataFile")[0].files[0]);
        formData.append('objSize', $("#inputGroupDataFile")[0].files[0].size);

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
                        var rows = $('#tableGroups tbody').children().length;

                        if (rows > 0) {
                            $('#tableGroups tbody > tr').remove();
                        }

                        $('#groupTablePager').empty();
                        loadGroupTableData();
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_SUCCESS,
                            title: 'Successfully added new group',
                            message: obj[1]
                        });
                    } else {
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new group',
                            message: obj[1]
                        });
                    }
                },
                error : function (data, errorText) {
                    $("#errormsg").html(errorText).show();
                }
            });
        }

        if ($("#inputGroupName").val() && $("#inputGroupDataFile").val()) {
            upload();
            $("#inputGroupDataFile").val("");
        } else {
            if (!$("#inputGroupName").val()){
                BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new group',
                            message: "Empty group name not allowed"
                        });
            } else if (!$("#inputGroupDataFile").val()) {
                BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new group',
                            message: "No file chosen"
                        });
            }
        }
    });
}

function groupConfigDelBtnEventHandler() {
    $("#groupDelBtn").on( "click", function() {

        function del(groupName) {
                $.ajax({
                    url: '/api/group?action=del&name=' + groupName,
                    type: 'POST',
                    cache: false,
                    contentType: false,
                    processData: false,
                    success: function (response) {

                        var obj = JSON.parse(response);

                        if (obj[0]) {
                            var rows = $('#tableGroups tbody').children().length;

                            if (rows > 0) {
                                $('#tableGroups tbody > tr').remove();
                            }

                            $('#groupTablePager').empty();
                            loadGroupTableData();
                            BootstrapDialog.show({
                                type: BootstrapDialog.TYPE_SUCCESS,
                                title: 'Successfully deleted group',
                                message: obj[1]
                            });
                        } else {
                            BootstrapDialog.show({
                                type: BootstrapDialog.TYPE_WARNING,
                                title: 'Error deleting group',
                                message: obj[1]
                            });
                        }
                    },
                    error : function (data, errorText) {
                        $("#errormsg").html(errorText).show();
                    }
                });
            }

        var selectedRows = $('#tableGroups').find('tbody').find('tr').has('input[type=checkbox]:checked')

        if (selectedRows) {
            $( selectedRows ).each( function( index, element ){
                del($(this).find('td').eq(1).text());
            });
        }
    });
}

function groupConfigCloseBtnEventHandler(groupName){

    $("#groupCfgCloseBtn" + groupName).on( "click", function() {
        $("#modalGroupCfg" + groupName).remove();
        $('.modal-backdrop').remove();
    });
}

function createGroupConfigTable(groups){

    var trHTML = '';

        $.each(groups, function (i, group) {

            trHTML +=
            "<tr id=groupId-" + group['groupId'] + ">" +
                "<td>" +
                "<input type=\"checkbox\" class=\"filled-in\" id=\"checkbox-" + group['groupId'] + "\">" +
                "<label for=\"checkbox-" + group['groupId'] + "\"class=\"label-table\"></label>" +
                "</td>" +
                "<td>" + group['groupName'] + "</td>" +
                "<td>" + group['groupDescr'] + "</td>" +
                "<td>" + group['groupConfigSource'] + "</td>" +
                "<td>" +
                    "<button id=\"groupCfg" + group['groupName'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-eye-open\"></button>" +
                "</td>"
            "</tr>"
        });
        $('#tableGroups').append(trHTML);

        $.each(groups, function (i, group) {
            $('#groupCfg' + group['groupName']).on("click", function(){
                    createGroupConfigModal(group['groupName']);
                    groupConfigCloseBtnEventHandler(group['groupName']);
                    loadGroupConfiguration(group['groupName']);
                    $("#modalGroupCfg" + group['groupName']).modal("show");
                });
        });
        $('#tableGroups tbody').pageTable({pagerSelector:'#groupTablePager',showPrevNext:true,hidePageNumbers:false,perPage:10});
}

function createGroupConfigModal(groupName){

  var groupConfigModal = "<div class=\"modal fade\" id=\"modalGroupCfg" + groupName + "\" role=\"dialog\">" +
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
          "<button type=\"button\" class=\"btn btn-default\" id=\"groupCfgCloseBtn" + groupName + "\">Close</button>"
        "</div>" +
      "</div>" +
    "</div>" +
  "</div";
  $('body').append(groupConfigModal);
}

function createGroupConfigAddModal(){

    var createGroupConfigAddModal = "<div class=\"modal fade\" id=\"modalGroupAddNew\" role=\"dialog\">" +
        "<div class=\"modal-dialog modal-lg\">" +
          //<!-- Modal content-->
          "<div class=\"modal-content\">" +
            "<div class=\"modal-header\">" +
              "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
              "<h4 class=\"modal-title\">Add new group configuration</h4>" +
            "</div>" +
            "<div class=\"modal-body\">" +
                "<form class=\"form-horizontal\" id=\"formGroupFileUpload\">" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputGroupName\" class=\"col-sm-2 control-label\">Group Name</label>" +
                    "<div class=\"col-sm-6\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputGroupName\" placeholder=\"New Group Name\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputGroupDescr\" class=\"col-sm-2 control-label\">Group Description</label>" +
                    "<div class=\"col-sm-6\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputGroupDescr\" placeholder=\"Group Description\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"comboBoxGroupStorage\" class=\"col-sm-2 control-label\">Storage</label>" +
                    "<div class=\"col-sm-4\">" +
                        "<select id=\"comboBoxGroupStorage\" class=\"form-control comboBoxStorage\" name=\"comboBoxGroupStorage\">" +
                            "<option value=\"\">Choose storage type</option>" +
                        "</select>" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputGroupDataFile\" class=\"col-sm-2 control-label\">Group Data File</label>" +
                    "<div class=\"col-sm-4\">" +
                      "<input type=\"file\" name=\"obj\" id=\"inputGroupDataFile\" placeholder=\"Group Data File\" accept=\".yml\">" +
                    "</div>" +
                  "</div>" +
                "</form>" +
            "</div>" +
            "<div class=\"modal-footer\">" +
              "<button type=\"button\" class=\"btn btn-default\" id=\"groupSaveBtn\">Save</button>" +
              "<button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Close</button>" +
            "</div>" +
          "</div>" +
        "</div>" +
    "</div>";
  $('body').append(createGroupConfigAddModal);
}

function loadGroups(elem) {

    function fetch() {
        $.ajax({
            url: '/api/group',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=all',
            success: function (response) {

                if ($(elem).has('option').length > 0 ){
                    $(elem).children('option').not(':first').remove();
                }

                if (response[0]){
                    $.each(response[1], function(key, value) {
                         $(elem)
                             .append($("<option></option>")
                             .attr("value", key)
                             .text(value['groupName']));
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

function loadGroupConfiguration(groupName) {

    function fetch() {
        $.ajax({
            url: '/api/group',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=config&name=' + groupName,
            success: function (response) {
                $("#textarea" + groupName).val(response[1]);
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

                if (response[0]) {
                    createGroupConfigTable(response[1]);
                } else {
                    BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error getting group information',
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