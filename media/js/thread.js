function toggle_post(id) {
    toggle('sum'+id, 'inline');
    toggle('post'+id, 'block');
}

function toggle_edit(id) {
    toggle('post_text'+id, 'block');
    toggle('post_edit'+id, 'block');
}

function toggle(id, type) {
    var e = document.getElementById(id);
    if(e.style.display == 'none')
        e.style.display = type;
    else
        e.style.display = 'none';
}

// --- yahoo connection stuff ---
function toggle_variable(action, oclass, oid, msgdivid) {
    // This function sends an RPC request to the server to toggle a
    // variable (usually a boolean).  The server response with text
    // to replace the button clicked and a status message.

    // TODO: oid should be renamed as oid
    var postData = 'action=' + action + '&oclass=' + oclass + '&oid=' + oid;
    var div = document.getElementById(action + oid);

    var handleSuccess = function(o) {
        if(o.responseText !== undefined) {
            res = eval('(' + o.responseText + ')');
            div.innerHTML = res['link'];
            document.getElementById(msgdivid).innerHTML = '<p class="rpc_message">' + res['msg'] + '</p>';
        }
    };

    var handleFailure = function(o) {
        var errordiv = document.getElementById("thread_rpc_msg_div");
        if(o.responseText !== undefined) {
            div.innerHTML = "<b>ERROR</b>";
            for (var n in o) {
                if (o.hasOwnProperty(n)) {
                    errordiv.innerHTML += o[n];
                }
            }
        }
    };

    var callback =
    {
      success:handleSuccess,
      failure:handleFailure,
      argument:[]
    };

    var request = YAHOO.util.Connect.asyncRequest('POST', '/snapboard/rpc/action/', callback, postData);
}

// thread level functions
function set_csticky(id) { toggle_variable('csticky', 'thread', id, 'thread_rpc_msg_div'); }
function set_gsticky(id) { toggle_variable('gsticky', 'thread', id, 'thread_rpc_msg_div'); }
function set_watch(id) { toggle_variable('watch', 'thread', id, 'thread_rpc_msg_div'); }

// post level function
function set_censor(id) { toggle_variable('censor', 'post', id, ('post_rpc_msg_div' + id));}
function set_abuse(id) { toggle_variable('abuse', 'post', id, ('post_rpc_msg_div' + id));}
