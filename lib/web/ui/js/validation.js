/*
DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
Copyright (c) 2018 Juniper Networks, Inc.
All rights reserved.
Use is subject to license terms.

Author: cklewar
*/


function valSaveBtnEventHandler(){

    $("#valSaveBtn").on( "click", function() {

        var data = {
            "username": $("#inputValUsername").val(),
            "password": $("#inputValPassword").val(),
        };

        function upload() {
            $.ajax({
                url: '/api/validation?action=add',
                type: 'POST',
                data: JSON.stringify(data),
                cache: false,
                dataType: 'json',
                contentType: 'application/json',
                processData: true,
                success: function (response) {

                    var obj = JSON.parse(response);

                    if (obj[0]) {
                        var rows = $('#tableValidation tbody').children().length;

                        if (rows > 0) {
                            $('#tableValidation tbody > tr').remove();
                        }

                        $('#validationTablePager').empty();
                        loadValidationTableData();
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_SUCCESS,
                            title: 'Successfully added new asset validation entry',
                            message: obj[1]
                        });

                    } else {
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new asset validation entry',
                            message: obj[1]
                        });
                    }
                },
                error : function (data, errorText) {
                    $("#errormsg").html(errorText).show();
                }
            });
        }

        if ($("#inputValUsername").val()) {
            upload();
        } else {
            if (!$("#inputValUsername").val()){
                BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new asset validation entry',
                            message: "Empty asset username / password not allowed"
                });
            }
        }
    });
}

function valDelBtnEventHandler() {
    $("#valDelBtn").on( "click", function() {

        function del(username) {

            $.ajax({
                url: '/api/validation?action=del',
                type: 'POST',
                data: JSON.stringify(data),
                cache: false,
                dataType: 'json',
                contentType: 'application/json',
                processData: true,
                success: function (response) {

                    var obj = JSON.parse(response);

                    if (obj[0]) {
                        var rows = $('#tableValidation tbody').children().length;

                        if (rows > 0) {
                            $('#tableValidation tbody > tr').remove();
                        }

                        $('#validationTablePager').empty();
                        loadValidationTableData();
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_SUCCESS,
                            title: 'Successfully deleted asset validation entry',
                            message: obj[1]
                        });

                    } else {
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error deleting asset validation entry',
                            message: obj[1]
                        });
                    }
                },
                error : function (data, errorText) {
                    $("#errormsg").html(errorText).show();
                }
            });
        }

        var selectedRows = $('#tableValidation').find('tbody').find('tr').has('input[type=checkbox]:checked')
        var data;

        if (selectedRows) {
            $( selectedRows ).each( function( index, element ){
                data = {
                    'username': $(this).find('td').eq(1).text(),
                };
                del($(this).find('td').eq(1).text());
            });
        }
    });
}

function createValidationTable(assets){
    var trHTML = '';

        $.each(assets, function (i, asset) {
            trHTML +=
            "<tr id=validationId-" + asset['id'] + ">" +
                "<td>" +
                "<input type=\"checkbox\" class=\"filled-in\" id=\"checkbox-" + asset['id'] + "\">" +
                "<label for=\"checkbox-" + asset['id'] + "\"class=\"label-table\"></label>" +
                "</td>" +
                "<td>" + asset['username'] + "</td>" +
                "<td>" + asset['password'] + "</td>" +
                "<td>" + asset['retries'] + "</td>" +
            "</tr>"
        });
        $('#tableValidation').append(trHTML);
        $('#tableValidation tbody').pageTable({pagerSelector:'#validationTablePager',showPrevNext:true,hidePageNumbers:false,perPage:10});
}

function createValidationAddModal(){

    var createValidationAddModal = "<div class=\"modal fade\" id=\"modalValidationAddNew\" role=\"dialog\">" +
        "<div class=\"modal-dialog modal-lg\">" +
          //<!-- Modal content-->
          "<div class=\"modal-content\">" +
            "<div class=\"modal-header\">" +
              "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
              "<h4 class=\"modal-title\">Add new asset validation entry</h4>" +
            "</div>" +
            "<div class=\"modal-body\">" +
                "<form class=\"form-horizontal\" id=\"formValidationCreate\">" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputValUsername\" class=\"col-sm-2 control-label\">Asset Username</label>" +
                    "<div class=\"col-sm-6\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputValUsername\" placeholder=\"New Asset validation entry\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputValPassword\" class=\"col-sm-2 control-label\">Asset Password</label>" +
                    "<div class=\"col-sm-6\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputValPassword\" placeholder=\"New Asset validation password\">" +
                    "</div>" +
                  "</div>" +
                "</form>" +
            "</div>" +
            "<div class=\"modal-footer\">" +
              "<button type=\"button\" class=\"btn btn-default\" id=\"valSaveBtn\">Save</button>" +
              "<button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Close</button>" +
            "</div>" +
          "</div>" +
        "</div>" +
    "</div>";
  $('body').append(createValidationAddModal);
}

function loadValidationTableData() {

    function fetch() {
        $.ajax({
            url: '/api/validation',
            type: 'GET',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=all',
            success: function (response) {

                if (response[0]) {
                    createValidationTable(response[1]);
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