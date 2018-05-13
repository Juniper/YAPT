/*
DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
Copyright (c) 2018 Juniper Networks, Inc.
All rights reserved.
Use is subject to license terms.

Author: cklewar
*/

function loadStorage(elem) {

    function fetch() {
        $.ajax({
            url: '/api/configsrc',
            dataType: 'json',
            contentType: 'application/json',
            data: 'action=sources',
            success: function (response) {

                if ($(elem).has('option').length > 0 ){
                    $(elem).children('option').not(':first').remove();
                }

                if (response[0]){

                    $.each(response[1], function(key, value) {
                         $(elem)
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