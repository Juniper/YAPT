/*
DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
Copyright (c) 2018 Juniper Networks, Inc.
All rights reserved.
Use is subject to license terms.

Author: cklewar
*/

function siteConfigSaveBtnEventHandler(){
    $("#siteSaveBtn").on( "click", function() {

        var data = {
            'siteId': $("#inputSiteId").val(),
            'siteName': $("#inputSiteName").val(),
            'siteDescr': $("#inputSiteDescr").val()
        };

        function upload() {
            $.ajax({
                url: '/api/site?action=add',
                type: 'POST',
                data: JSON.stringify(data),
                cache: false,
                dataType: 'json',
                contentType: 'application/json',
                processData: true,
                success: function (response) {

                    var obj = JSON.parse(response);

                    if (obj[0]) {
                        var rows = $('#tableSites tbody').children().length;

                        if (rows > 0) {
                            $('#tableSites tbody > tr').remove();
                        }

                        $('#siteTablePager').empty();
                        loadSiteTableData();
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_SUCCESS,
                            title: 'Successfully added new site',
                            message: obj[1]
                        });
                    } else {
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new site',
                            message: obj[1]
                        });
                    }
                },
                error : function (data, errorText) {
                    $("#errormsg").html(errorText).show();
                }
            });
        }

        if ($("#inputSiteName").val()) {
            upload();
        } else {
            if (!$("#inputSiteName").val()){
                BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new site',
                            message: "Empty site name not allowed"
                        });
            }
        }
    });
}

function assetConfigSaveBtnEventHandler(siteId){

    $("#assetSaveBtn" + siteId).on( "click", function() {

        var data = {
            "assetSiteId": siteId,
            "assetSerial": $("#inputAssetSerial").val(),
            "assetConfigId": $("#inputAssetConfigId").val(),
            "assetDescr": $("#inputAssetDescr").val(),
        };

        function upload() {
            $.ajax({
                url: '/api/asset?action=add',
                type: 'POST',
                data: JSON.stringify(data),
                cache: false,
                dataType: 'json',
                contentType: 'application/json',
                processData: true,
                success: function (response) {

                    var obj = JSON.parse(response);

                    if (obj[0]) {
                        var rows = $('#asset-' + siteId + ' tbody').children().length;

                        if (rows > 0) {
                            $('#asset-' + siteId + ' tbody > tr').remove();
                        }

                        loadAssetTableData(siteId);
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_SUCCESS,
                            title: 'Successfully added new asset',
                            message: obj[1]
                        });
                    } else {
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new asset',
                            message: obj[1]
                        });
                    }
                },
                error : function (data, errorText) {
                    $("#errormsg").html(errorText).show();
                }
            });
        }

        if ($("#inputAssetConfigId").val()) {
            upload();
        } else {
            if (!$("#inputAssetConfigId").val()){
                BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new asset',
                            message: "Empty asset config id not allowed"
                        });
            }
        }
    });
}

function siteConfigDelBtnEventHandler() {
    $("#siteDelBtn").on( "click", function() {

        function del(siteId) {

            $.ajax({
                url: '/api/site?action=del&name=' + siteId,
                type: 'POST',
                data: JSON.stringify(data),
                cache: false,
                dataType: 'json',
                contentType: 'application/json',
                processData: true,
                success: function (response) {

                    var obj = JSON.parse(response);

                    if (obj[0]) {
                        var rows = $('#tableSites tbody').children().length;

                        if (rows > 0) {
                            $('#tableSites tbody > tr').remove();
                        }

                        $('#siteTablePager').empty();
                        loadSiteTableData();
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_SUCCESS,
                            title: 'Successfully deleted site',
                            message: obj[1]
                        });

                    } else {
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error deleting site',
                            message: obj[1]
                        });
                    }
                },
                error : function (data, errorText) {
                    $("#errormsg").html(errorText).show();
                }
            });
        }

        var selectedRows = $('#tableSites').find('tbody').find('tr').has('input[type=checkbox]:checked')
        var data;

        if (selectedRows) {
            $( selectedRows ).each( function( index, element ){
                data = {
                    'siteId': $(this).find('td').eq(2).text(),
                };
                del($(this).find('td').eq(2).text());
            });
        }
    });
}

function assetConfigCloseBtnEventHandler(siteId){

    $("#assetCloseBtn" + siteId).on( "click", function() {
        $("#modalAssetAddNew" + siteId).remove();
        $('.modal-backdrop').remove();
    });
}

function createSiteConfigTable(sites){
    var trHTML = '';
        $.each(sites, function (i, site) {
            trHTML +=
            "<tr id=siteId-" + site['siteId'] + ">" +
                "<td>" +
                    "<input type=\"checkbox\" class=\"filled-in\" id=\"checkbox-" + site['siteId'] + "\">" +
                    "<label for=\"checkbox-" + site['siteId'] + "\"class=\"label-table\"></label>" +
                "</td>" +
                "<td>" +
                    "<button class=\"btn btn-default btn-xs\" data-toggle=\"collapse\" data-target=\"#data-" + site['siteId'] + "\" class=\"accordion-toggle\">" +
                        "<span class=\"glyphicon glyphicon-tasks\"></span>" +
                    "</button>" +
                "</td>" +
                "<td>" + site['siteId'] + "</td>" +
                "<td>" + site['siteName'] + "</td>" +
                "<td>" + site['siteDescr'] + "</td>" +
                "<td><button id=\"assetAddBtn" + site['siteId'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-plus\"></button></td>" +
            "</tr>" +
            "<tr>" +
            "<td colspan=\"9\" class=\"hiddenRow\">" +
                "<div class=\"accordian-body collapse\" id=\"data-" + site['siteId'] + "\">" +
                    "<table class=\"table table-hover\" id=\"asset-" + site['siteId'] + "\">" +
                        "<thead>" +
                            "<th>Asset Serial</th><th>Asset Config ID</th><th>Asset Description</th>" +
                            "</tr>" +
                        "</thead>" +
                        "<tbody>" +
                        "</tbody>" +
                    "</table>" +
                "</div>" +
            "</td>" +
        "</tr>";
        });
        $('#tableSites').append(trHTML);

        $.each(sites, function (i, site) {
            trHTML = '';
            $.each(site['assets'], function (i, asset) {
                trHTML += "<tr><td>" + asset['assetSerial'] + "</td>" + "<td>" + asset['assetConfigId'] + "</td><td>" + asset['assetDescr'] + "</td></tr>";
            });
            $("#asset-" + site['siteId'] + " > tbody").append(trHTML);
        });

        $.each(sites, function (i, site) {

            $('#assetAddBtn' + site['siteId']).on("click", function(){
                createAssetConfigAddModal(site['siteId']);
                assetConfigSaveBtnEventHandler(site['siteId']);
                assetConfigCloseBtnEventHandler(site['siteId']);
                $("#modalAssetAddNew" + site['siteId']).modal("show");
            });
        });
        $('#tableSites > tbody').pageTable({pagerSelector:'#siteTablePager',showPrevNext:true,hidePageNumbers:false,perPage:10});
}

function createAssetConfigTable(assets, siteId){
    var trHTML = '';

    $.each(assets, function (i, asset) {
        trHTML +=
        "<tr><td>" + asset['assetSerial'] + "</td>" + "<td>" + asset['assetConfigId'] + "</td><td>" + asset['assetDescr'] + "</td></tr>";
    });

    if ($("#asset-" + siteId).has( "tbody" )){
        $("#asset-" + siteId + " tbody").append(trHTML);
    } else {
        console.log('no tbody');
    }
}

function createSiteConfigAddModal(){

    var createSiteConfigAddModal = "<div class=\"modal fade\" id=\"modalSiteAddNew\" role=\"dialog\">" +
        "<div class=\"modal-dialog modal-lg\">" +
          //<!-- Modal content-->
          "<div class=\"modal-content\">" +
            "<div class=\"modal-header\">" +
              "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
              "<h4 class=\"modal-title\">Add new site configuration</h4>" +
            "</div>" +
            "<div class=\"modal-body\">" +
                "<form class=\"form-horizontal\" id=\"formSiteCreate\">" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputSiteId\" class=\"col-sm-2 control-label\">Site Id</label>" +
                    "<div class=\"col-sm-6\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputSiteId\" placeholder=\"New Site Id\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputSiteName\" class=\"col-sm-2 control-label\">Site Name</label>" +
                    "<div class=\"col-sm-6\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputSiteName\" placeholder=\"New Site Name\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputSiteDescr\" class=\"col-sm-2 control-label\">Site Description</label>" +
                    "<div class=\"col-sm-6\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputSiteDescr\" placeholder=\"Site Description\">" +
                    "</div>" +
                  "</div>" +
                "</form>" +
            "</div>" +
            "<div class=\"modal-footer\">" +
              "<button type=\"button\" class=\"btn btn-default\" id=\"siteSaveBtn\">Save</button>" +
              "<button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Close</button>" +
            "</div>" +
          "</div>" +
        "</div>" +
    "</div>";
  $('body').append(createSiteConfigAddModal);
}

function createAssetConfigAddModal(siteId){

    var createAssetConfigAddModal = "<div class=\"modal fade\" id=\"modalAssetAddNew" + siteId + "\"  role=\"dialog\">" +
        "<div class=\"modal-dialog modal-lg\">" +
          //<!-- Modal content-->
          "<div class=\"modal-content\">" +
            "<div class=\"modal-header\">" +
              "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
              "<h4 class=\"modal-title\">Add new asset to site</h4>" +
            "</div>" +
            "<div class=\"modal-body\">" +
                "<form class=\"form-horizontal\" id=\"formAssetAdd\">" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputAssetSiteId\" class=\"col-sm-2 control-label\">Asset Site Id</label>" +
                    "<div class=\"col-sm-8\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputAssetSiteId\" placeholder=\"New Asset Site Id\" value=\"" + siteId + "\" readonly>" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputAssetSerial\" class=\"col-sm-2 control-label\">Asset Serial</label>" +
                    "<div class=\"col-sm-8\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputAssetSerial\" placeholder=\"Asset Serial\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputAssetConfigId\" class=\"col-sm-2 control-label\">Asset Config ID</label>" +
                    "<div class=\"col-sm-8\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputAssetConfigId\" placeholder=\"Asset Config ID\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputAssetDescr\" class=\"col-sm-2 control-label\">Asset Description</label>" +
                    "<div class=\"col-sm-8\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputAssetDescr\" placeholder=\"Asset Description\">" +
                    "</div>" +
                  "</div>" +
                "</form>" +
            "</div>" +
            "<div class=\"modal-footer\">" +
              "<button type=\"button\" class=\"btn btn-default\" id=\"assetSaveBtn" + siteId + "\">Save</button>" +
              "<button type=\"button\" class=\"btn btn-default\" id=\"assetCloseBtn" + siteId + "\">Close</button>" +
            "</div>" +
          "</div>" +
        "</div>" +
    "</div>";
  $('body').append(createAssetConfigAddModal);
}

function loadSiteTableData() {

    function fetch() {
        $.ajax({
            url: '/api/site',
            dataType: 'json',
            data: 'siteId=all',
            success: function (response) {

                if (response[0]) {
                    createSiteConfigTable(response[1]);
                } else {
                    BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error getting site information',
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

function loadAssetTableData(siteId) {

    function fetch() {
        $.ajax({
            url: '/api/asset',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=getBySiteId&serial=' + siteId,
            success: function (response) {

                if (response[0]) {
                    createAssetConfigTable(response[1], siteId);
                } else {
                    BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error getting asset information',
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