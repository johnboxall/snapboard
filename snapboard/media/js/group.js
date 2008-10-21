function do_post (action, data, conf, conf_arg) {
    if (conf && !conf(conf_arg)) {
        return false;
    }
    var s = [];
    for (key in data) {
        s.push(encodeURIComponent(key) + '=' + encodeURIComponent(data[key]));
    }
    post_data = s.join('&').replace(/%20/g, '+');
    
    var handleSuccess = function(o) {
        if(o.responseText !== undefined) {
            if (o.responseText == 'ok') {
                // reload the page
                window.location = '';
            }
        }
    };

    var callback = {success:handleSuccess, failure:function (o) {}, argument: []};
    var request = YAHOO.util.Connect.asyncRequest('POST', action, callback, post_data);
    return false;
}

function confirm_remove_user (username) {
    return confirm(interpolate(gettext("Are you sure you want to remove the user %s from this group?"), [username]));
}

function confirm_remove_ar (username) {
    return confirm(interpolate(gettext("Are you sure you want to remove the admin rights of %s for the group?"), [username]));
}

function confirm_cancel_invitation (arg) {
    return confirm(gettext("Are you sure you want to cancel this invitation ?"));
}

function confirm_promote (username) {
    return confirm(interpolate(gettext("Are you sure you want to promote %s to administrator of this group?"), [username]));
}

