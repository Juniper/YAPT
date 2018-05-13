/*
DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
Copyright (c) 2018 Juniper Networks, Inc.
All rights reserved.
Use is subject to license terms.

Author: cklewar
*/

function imageConfigSaveBtnEventHandler(){
    $("#imageSaveBtn").on( "click", function() {

        var formData = new FormData();

        formData.append('name', $("#inputImageName").val());
        formData.append('descr', $("#inputImageDescr").val());
        formData.append('type', 'image');
        formData.append('obj', $("#inputImageDataFile")[0].files[0]);

        function upload() {
            $.ajax({
                xhr: function() {
                    var xhr = new window.XMLHttpRequest();

                    xhr.upload.addEventListener("progress", function(evt) {
                      if (evt.lengthComputable) {
                        var percentComplete = evt.loaded / evt.total;
                        percentComplete = parseInt(percentComplete * 100);
                        $("#imageUploadProgressBar").css("width", percentComplete + "%").attr("aria-valuenow", percentComplete);
                        $("#imageUploadProgressSpan").text(percentComplete + "% Complete");

                        //if (percentComplete === 100) {
                        //    console.log('Done');
                        //}
                      }
                    }, false);
                    return xhr;
                  },
                url: '/api/upload',
                type: 'POST',
                data: formData,
                cache: false,
                contentType: false,
                processData: false,
                success: function (response) {

                    var obj = JSON.parse(response);

                    if (obj[0]) {
                        var rows = $('#tableImages tbody').children().length;

                        if (rows > 0) {
                            $('#tableImages tbody > tr').remove();
                        }

                        $('#imageTablePager').empty();
                        loadImageTableData();
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_SUCCESS,
                            title: 'Successfully added new image',
                            message: obj[1]
                        });
                    } else {
                        BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new image',
                            message: obj[1]
                        });
                    }
                },
                error : function (data, errorText) {
                    $("#errormsg").html(errorText).show();
                }
            });
        }

        if ($("#inputImageName").val() && $("#inputImageDataFile").val()) {
            upload();
            $("#inputImageDataFile").val("");
        } else {
            if (!$("#inputImageName").val()){
                BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new image',
                            message: "Empty image name not allowed"
                        });
            } else if (!$("#inputGroupDataFile").val()) {
                BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error adding new image',
                            message: "No file chosen"
                        });
            }
        }
    });
}

function imageConfigDelBtnEventHandler() {
    $("#imageDelBtn").on( "click", function() {

        function del(imageName) {
                $.ajax({
                    url: '/api/image?action=del&name=' + imageName,
                    type: 'POST',
                    cache: false,
                    contentType: false,
                    processData: false,
                    success: function (response) {

                        var obj = JSON.parse(response);

                        if (obj[0]) {
                            var rows = $('#tableImages tbody').children().length;

                            if (rows > 0) {
                                $('#tableImages tbody > tr').remove();
                            }

                            $('#imageTablePager').empty();
                            loadImageTableData();
                            BootstrapDialog.show({
                                type: BootstrapDialog.TYPE_SUCCESS,
                                title: 'Successfully deleted image',
                                message: obj[1]
                            });
                        } else {
                            BootstrapDialog.show({
                                type: BootstrapDialog.TYPE_WARNING,
                                title: 'Error deleting image',
                                message: obj[1]
                            });
                        }
                    },
                    error : function (data, errorText) {
                        $("#errormsg").html(errorText).show();
                    }
                });
            }

        var selectedRows = $('#tableImages').find('tbody').find('tr').has('input[type=checkbox]:checked')

        if (selectedRows) {
            $( selectedRows ).each( function( index, element ){
                del($(this).find('td').eq(2).text());
            });
        }
    });
}

function createImageConfigTable(images){
    var trHTML = '';

        $.each(images, function (i, image) {
            trHTML +=
            "<tr id=imageId-" + image['imageId'] + ">" +
                "<td>" +
                "<input type=\"checkbox\" class=\"filled-in\" id=\"checkbox-" + image['imageId'] + "\">" +
                "<label for=\"checkbox-" + image['imageId'] + "\"class=\"label-table\"></label>" +
                "</td>" +
                "<td>" + image['imageId'] + "</td>" +
                "<td>" + image['imageName'] + "</td>" +
                "<td>" + image['imageDescr'] + "</td>" +
            "</tr>"
        });
        $('#tableImages').append(trHTML);
}

function createImageConfigAddModal(){

    var createImageConfigAddModal = "<div class=\"modal fade\" id=\"modalImageAddNew\" role=\"dialog\">" +
        "<div class=\"modal-dialog modal-lg\">" +
          //<!-- Modal content-->
          "<div class=\"modal-content\">" +
            "<div class=\"modal-header\">" +
              "<button type=\"button\" class=\"close\" data-dismiss=\"modal\">&times;</button>" +
              "<h4 class=\"modal-title\">Add new software image </h4>" +
            "</div>" +
            "<div class=\"modal-body\">" +
                "<form class=\"form-horizontal\" id=\"formImageFileUpload\">" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputImageName\" class=\"col-sm-2 control-label\">Image Name</label>" +
                    "<div class=\"col-sm-6\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputImageName\" placeholder=\"New Image Name\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputImageDescr\" class=\"col-sm-2 control-label\">Image Description</label>" +
                    "<div class=\"col-sm-6\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputImageDescr\" placeholder=\"Image Description\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputImageDataFile\" class=\"col-sm-2 control-label\">Image Data File</label>" +
                    "<div class=\"col-sm-6\">" +
                      "<input type=\"file\" name=\"obj\" id=\"inputImageDataFile\" placeholder=\"Image File\" accept=\".tgz\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"imageUploadProgressBar\" class=\"col-sm-2 control-label\">Progress</label>" +
                    "<div class=\"col-sm-6\">" +
                        "<div class=\"progress\" style=\"height: 25px;\">" +
                            "<div class=\"progress-bar progress-bar bg-info\" id=\"imageUploadProgressBar\" role=\"progressbar\" aria-valuenow=\"0\" aria-valuemin=\"0\" aria-valuemax=\"100\" style=\"width: 0%\">" +
                                "<span id=\"imageUploadProgressSpan\">0% Complete</span>" +
                            "</div>" +
                        "</div>" +
                    "</div>" +
                  "</div>" +
                "</form>" +
            "</div>" +
            "<div class=\"modal-footer\">" +
              "<button type=\"button\" class=\"btn btn-default\" id=\"imageSaveBtn\">Save</button>" +
              "<button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Close</button>" +
            "</div>" +
          "</div>" +
        "</div>" +
    "</div>";
  $('body').append(createImageConfigAddModal);
}

function loadImageTableData() {

    function fetch() {
        $.ajax({
            url: '/api/image',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=all',
            success: function (response) {

                if (response[0]) {
                    createImageConfigTable(response[1]);
                } else {
                    BootstrapDialog.show({
                            type: BootstrapDialog.TYPE_WARNING,
                            title: 'Error getting image information',
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