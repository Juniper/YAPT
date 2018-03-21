$.fn.pageTable = function(opts){

    var $this = this,
        defaults = {
            perPage: 7,
            showPrevNext: false,
            hidePageNumbers: false
        },
        settings = $.extend(defaults, opts);

    var listElement = $this;
    var perPage = settings.perPage;
    var children = listElement.children();
    var pager = $('.pager');

    if (typeof settings.childSelector!="undefined") {
        children = listElement.find(settings.childSelector);
    }

    if (typeof settings.pagerSelector!="undefined") {
        pager = $(settings.pagerSelector);
    }

    var numItems = children.length;
    var numPages = Math.ceil(numItems/perPage);

    pager.data("curr",0);

    if (settings.showPrevNext){
        $('<li><a href="#" class="prev_link">«</a></li>').appendTo(pager);
    }

    var curr = 0;
    while(numPages > curr && (settings.hidePageNumbers==false)){
        $('<li><a href="#" class="page_link">'+(curr+1)+'</a></li>').appendTo(pager);
        curr++;
    }

    if (settings.showPrevNext){
        $('<li><a href="#" class="next_link">»</a></li>').appendTo(pager);
    }

    pager.find('.page_link:first').addClass('active');
    pager.find('.prev_link').hide();

    if (numPages<=1) {
        pager.find('.next_link').hide();
    }
      pager.children().eq(1).addClass("active");

    children.hide();
    children.slice(0, perPage).show();

    pager.find('li .page_link').click(function(){
        var clickedPage = $(this).html().valueOf()-1;
        goTo(clickedPage,perPage);
        return false;
    });
    pager.find('li .prev_link').click(function(){
        previous();
        return false;
    });
    pager.find('li .next_link').click(function(){
        next();
        return false;
    });

    function previous(){
        var goToPage = parseInt(pager.data("curr")) - 1;
        goTo(goToPage);
    }

    function next(){
        goToPage = parseInt(pager.data("curr")) + 1;
        goTo(goToPage);
    }

    function goTo(page){
        var startAt = page * perPage,
            endOn = startAt + perPage;

        children.css('display','none').slice(startAt, endOn).show();

        if (page>=1) {
            pager.find('.prev_link').show();
        }
        else {
            pager.find('.prev_link').hide();
        }

        if (page<(numPages-1)) {
            pager.find('.next_link').show();
        }
        else {
            pager.find('.next_link').hide();
        }

        pager.data("curr",page);
        pager.children().removeClass("active");
        pager.children().eq(page+1).addClass("active");

    }
};

function updateDeviceProvProgress(device){
    //console.log(device.taskProgress, device.taskKey, device.taskKeyState);
    $("#deviceProvProgressBar-" + device.deviceSerial).css("width", device.taskProgress + "%").text(device.taskProgress + "%");
}

function deviceConfigLoadCfgBtnEventHandler(device){
    $( "#modal" + device.deviceSerial).on( "click", function() {
        var modal = $('#modal' + device.deviceSerial);
        modal.find('.modal-title').text("Device Name: " + device.deviceName + " ---- Device Serial: " + device.deviceSerial);
        $( "#textarea" + device.deviceSerial).val(device.deviceConfiguration);
    });
}

function groupConfigSaveBtnEventHandler(){
    $("#groupSaveBtn").on( "click", function() {

        var formData = new FormData();

        formData.append('name', $("#inputGroupName").val());
        formData.append('descr', $("#inputGroupDescr").val());
        formData.append('type', 'group');
        formData.append('configSource', $("#comboBoxGroupConfigSource option:selected").text());
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
                del($(this).find('td').eq(2).text());
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

function templateConfigSaveBtnEventHandler(){
    $("#templateSaveBtn").on( "click", function() {

        var formData = new FormData();

        formData.append('name', $("#inputTemplateName").val());
        formData.append('descr', $("#inputTemplateDescr").val());
        formData.append('type', 'template');
        formData.append('group', $("#comboBoxTemplateDevGroup option:selected").text());
        formData.append('configSource', $("#comboBoxTemplateConfigSource option:selected").text());
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
                del($(this).find('td').eq(2).text());
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

function siteConfigSaveBtnEventHandler(){
    $("#siteSaveBtn").on( "click", function() {

        var data = {
            'siteId': $("#inputSiteId").val(),
            'siteName': $("#inputSiteName").val(),
            'siteDescr': $("#inputSiteDescr").val()
        };

        function upload() {
            $.ajax({
                url: '/api/site?action=add&name=' + $("#inputSiteName").val(),
                type: 'POST',
                data: JSON.stringify(data),
                cache: false,
                contentType: 'application/json',
                processData: true,
                success: function (response) {

                    var obj = JSON.parse(response);

                    if (obj[0]) {
                        var rows = $('#tableSites tbody').children().length;

                        if (rows > 0) {
                            $('#tableSites tbody > tr').remove();
                        }

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

function siteConfigDelBtnEventHandler() {
    $("#siteDelBtn").on( "click", function() {

        function del(siteId) {
            console.log('inside site del button');
            $.ajax({
                url: '/api/site?action=del&name=' + siteId,
                type: 'POST',
                data: JSON.stringify(data),
                cache: false,
                contentType: 'application/json',
                processData: true,
                success: function (response) {

                    var obj = JSON.parse(response);

                    if (obj[0]) {
                        var rows = $('#tableSites tbody').children().length;

                        if (rows > 0) {
                            $('#tableSites tbody > tr').remove();
                        }

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

function assetConfigCloseBtnEventHandler(siteId){

    $("#assetCloseBtn" + siteId).on( "click", function() {
        $("#modalAssetAddNew" + siteId).remove();
        $('.modal-backdrop').remove();
    });
}

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

function serviceConfigCloseBtnEventHandler(serviceName){

    $("#serviceCfgCloseBtn" + serviceName).on( "click", function() {
        $("#modalServiceCfg" + serviceName).remove();
        $('.modal-backdrop').remove();
    });
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

function createGroupConfigTable(groups){
    var trHTML = '';

        $.each(groups, function (i, group) {
            trHTML +=
            "<tr id=groupId-" + group['groupId'] + ">" +
                "<td>" +
                "<input type=\"checkbox\" class=\"filled-in\" id=\"checkbox-" + group['groupId'] + "\">" +
                "<label for=\"checkbox-" + group['groupId'] + "\"class=\"label-table\"></label>" +
                "</td>" +
                "<td>" + group['groupId'] + "</td>" +
                "<td>" + group['groupName'] + "</td>" +
                "<td>" + group['groupDescr'] + "</td>" +
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

function createTemplateConfigTable(templates){
    var trHTML = '';

        $.each(templates, function (i, template) {
            trHTML +=
            "<tr id=templateId-" + template['templateId'] + ">" +
                "<td>" +
                "<input type=\"checkbox\" class=\"filled-in\" id=\"checkbox-" + template['templateId'] + "\">" +
                "<label for=\"checkbox-" + template['templateId'] + "\"class=\"label-table\"></label>" +
                "</td>" +
                "<td>" + template['templateId'] + "</td>" +
                "<td>" + template['templateName'] + "</td>" +
                "<td>" + template['templateDescr'] + "</td>" +
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
                    "<button id=\"serviceStartBtn" + service['serviceName'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-play\" data-toggle=\"modal\" data-target=\"#modalServiceMod" + service['serviceName'] + "\"></button>" +
                    "<button id=\"serviceStopBtn" + service['serviceName'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-stop\" data-toggle=\"modal\" data-target=\"#modalServiceMod" + service['serviceName'] + "\"></button>" +
                    "<button id=\"serviceRestartBtn" + service['serviceName'] + "\" type=\"button\" class=\"btn btn-default btn-sm glyphicon glyphicon-refresh\" data-toggle=\"modal\" data-target=\"#modalServiceMod" + service['serviceName'] + "\"></button>" +
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
                    createServiceConfigModal(service['serviceName']);
                    serviceConfigCloseBtnEventHandler(service['serviceName']);
                    loadServiceConfiguration(service['serviceName']);
                    $("#modalServiceCfg" + service['serviceName']).modal("show");
            });
            $('#serviceStopBtn' + service['serviceName']).on("click", function(){
                    createServiceConfigModal(service['serviceName']);
                    serviceConfigCloseBtnEventHandler(service['serviceName']);
                    loadServiceConfiguration(service['serviceName']);
                    $("#modalServiceCfg" + service['serviceName']).modal("show");
            });
            $('#serviceRestartBtn' + service['serviceName']).on("click", function(){
                    createServiceConfigModal(service['serviceName']);
                    serviceConfigCloseBtnEventHandler(service['serviceName']);
                    loadServiceConfiguration(service['serviceName']);
                    $("#modalServiceCfg" + service['serviceName']).modal("show");
            });
        });
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
                    "<div class=\"col-sm-8\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputGroupName\" placeholder=\"New Group Name\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputGroupDescr\" class=\"col-sm-2 control-label\">Group Description</label>" +
                    "<div class=\"col-sm-8\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputGroupDescr\" placeholder=\"Group Description\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"comboBoxGroupConfigSource\" class=\"col-sm-2 control-label\">Config Source</label>" +
                    "<div class=\"col-sm-4\">" +
                        "<select id=\"comboBoxGroupConfigSource\" class=\"form-control comboBoxConfigSource\" name=\"comboBoxGroupConfigSource\">" +
                            "<option value=\"\">Choose configuration source type</option>" +
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
                    "<label for=\"inputTemplateName\" class=\"col-sm-2 control-label\">Template Name</label>" +
                    "<div class=\"col-sm-8\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputTemplateName\" placeholder=\"New Template Name\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputTemplateDescr\" class=\"col-sm-2 control-label\">Template Description</label>" +
                    "<div class=\"col-sm-8\">" +
                      "<input type=\"text\" class=\"form-control\" id=\"inputTemplateDescr\" placeholder=\"Template Description\">" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"comboBoxTemplateConfigSource\" class=\"col-sm-2 control-label\">Config Source</label>" +
                    "<div class=\"col-sm-4\">" +
                        "<select id=\"comboBoxTemplateConfigSource\" class=\"form-control comboBoxConfigSource\" name=\"comboBoxTemplateConfigSource\">" +
                            "<option value=\"\">Choose configuration source type</option>" +
                        "</select>" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"comboBoxTemplateDevGroup\" class=\"col-sm-2 control-label\">Device Group</label>" +
                    "<div class=\"col-sm-4\">" +
                        "<select id=\"comboBoxTemplateDevGroup\" class=\"form-control\" name=\"comboBoxTemplateDevGroup\">" +
                            "<option value=\"\">Choose device group</option>" +
                        "</select>" +
                    "</div>" +
                  "</div>" +
                  "<div class=\"form-group\">" +
                    "<label for=\"inputTemplateDataFile\" class=\"col-sm-2 control-label\">Template Data File</label>" +
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
  loadGroups();
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

function initialize(){

    //add modal
    createGroupConfigAddModal();
    createTemplateConfigAddModal();
    createImageConfigAddModal();
    createSiteConfigAddModal();

    //add config sources to cmobobox
    loadConfigSources();

    //add event handler
    groupConfigSaveBtnEventHandler();
    groupConfigDelBtnEventHandler();
    templateConfigSaveBtnEventHandler();
    templateConfigDelBtnEventHandler();
    imageConfigSaveBtnEventHandler();
    imageConfigDelBtnEventHandler();
    siteConfigSaveBtnEventHandler();
    siteConfigDelBtnEventHandler();

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

function loadServiceTableData() {

    function fetch() {
        $.ajax({
            url: '/api/service',
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

function loadConfigSources() {

    function fetch() {
        $.ajax({
            url: '/api/configsrc',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=sources',
            success: function (response) {

                if (response[0]){
                    $.each(response[1], function(key, value) {
                         $('.comboBoxConfigSource')
                             .append($("<option></option>")
                             .attr("value", key)
                             .text(value));
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

function loadGroups() {

    function fetch() {
        $.ajax({
            url: '/api/group',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=all',
            success: function (response) {

                if (response[0]){
                    $.each(response[1], function(key, value) {
                         $('#comboBoxTemplateDevGroup')
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
            dataType: 'text',
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

function loadTemplateConfiguration(templateName) {

    function fetch() {
        $.ajax({
            url: '/api/template',
            dataType: 'text',
            contentType: 'application/json',
            data: 'action=config&name=' + templateName,
            success: function (response) {
                $("#textarea" + templateName).val(response);
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

