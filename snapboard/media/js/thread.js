
function toggle_post(id) {
    toggle('snap_post_sum'+id, 'inline');
    toggle('snap_post_view'+id, 'block');
}

function toggle_edit(id) {
    //toggle('post_text'+id, 'block');
    toggle('snap_post_text'+id, 'block');
    toggle('snap_post_edit'+id, 'block');
}

function toggle(id, type) {
    var e = document.getElementById(id);
    if(e.style.display == 'none')
        e.style.display = type;
    else
        e.style.display = 'none';
}


function preview(form_id) {
    urlq = SNAPBOARD_URLS.rpc_preview;
    form = document.getElementById(form_id);
    text = form.post.value;
    div_preview = document.getElementById('snap_preview_addpost');
    var handleSuccess = function(o) {
        if(o.responseText !== undefined) {
            res = eval('(' + o.responseText + ')');
            div_preview.innerHTML = res['preview'];
            div_preview.parentNode.style.display = 'block';
        }
    };

    var handleFailure = function(o) {
        var errordiv = document.getElementById("thread_rpc_feedback");
        if(o.responseText !== undefined) {
            div_preview.innerHTML = gettext("There was an error previewing your post.");
            div_preview.parentNode.style.display = 'block';
        }
    };
    var callback = {success:handleSuccess, failure:handleFailure, argument: []};
    YAHOO.util.Connect.setDefaultPostHeader(false);
    YAHOO.util.Connect.initHeader('Content-Type', 'text/plain', true);
    var request = YAHOO.util.Connect.asyncRequest('POST', urlq, callback, text);
}


function revision(orig_id, show_id) {
    urlq = SNAPBOARD_URLS.rpc_postrev + '?orig=' + orig_id + '&show=' + show_id;

    div_text = document.getElementById('snap_post_text' + orig_id)
    div_links = document.getElementById('post_revision_links' + orig_id)

    var handleSuccess = function(o) {
        if(o.responseText !== undefined) {
            res = eval('(' + o.responseText + ')');
            div_text.innerHTML = res['text'];

            // create links content
            links_html = '';

            if(res['prev_id'] !== '') {
                links_html += '<a href="#post' + orig_id + '" onClick="revision(\'';
                //links_html += '<a href="#" onClick="revision(\'';
                links_html += orig_id + '\',\'' + res['prev_id'];
                links_html += '\');">&#171; ' + gettext('previous') + '</a>';
            }
            links_html += ' <b style="color: #c00;">' + gettext('This message has been revised') + '</b> '
            if(res['rev_id'] !== '') {
                links_html += '<a href="#post' + orig_id + '" onClick="revision(\'';
                //links_html += '<a href="#" onClick="revision(\'';
                links_html += orig_id + '\',\'' + res['rev_id'];
                links_html += '\');">' + gettext('next') + ' &#187;</a>';
            }
            div_links.innerHTML = links_html;
        }
    };

    var handleFailure = function(o) {
        var errordiv = document.getElementById("thread_rpc_feedback");
        if(o.responseText !== undefined) {
            for (var n in o) {
                if (o.hasOwnProperty(n)) {
                    errordiv.innerHTML += o[n];
                }
            }
        }
    };

    var callback = {
      success:handleSuccess,
      failure:handleFailure,
      argument: []
    };

    var request = YAHOO.util.Connect.asyncRequest('GET', urlq, callback, null);
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
        var errordiv = document.getElementById("thread_rpc_feedback");
        if(o.responseText !== undefined) {
            div.innerHTML = "<b>" + gettext('ERROR') + "</b>";
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

    var request = YAHOO.util.Connect.asyncRequest('POST', SNAPBOARD_URLS.rpc_action, callback, postData);
}

// thread level functions
function set_csticky(id) { toggle_variable('csticky', 'thread', id, 'thread_rpc_feedback'); }
function set_gsticky(id) { toggle_variable('gsticky', 'thread', id, 'thread_rpc_feedback'); }
function set_watch(id) { toggle_variable('watch', 'thread', id, 'thread_rpc_feedback'); }
function set_close(id) { toggle_variable('close', 'thread', id, 'thread_rpc_feedback'); }

// post level function
function set_censor(id) { toggle_variable('censor', 'post', id, ('post_rpc_feedback' + id));}
function set_abuse(id) { toggle_variable('abuse', 'post', id, ('post_rpc_feedback' + id));}

// get the source text of a message to quote it
function get_post_to_quote(id, cb) {
    var postData = 'action=quote&oid=' + id;
    var callback = {
        success: function (o) {
            if(o.responseText) {
                res = eval('(' + o.responseText + ')'); // FIXME: use a JSON parser
                cb(res['author'], res['text']);
            }
        },
        failure: function (o) { },
        argument:[]
    };
    YAHOO.util.Connect.asyncRequest('POST', SNAPBOARD_URLS.rpc_action, callback, postData);
}


/* =======================================================================
* Time Since
* January 16, 2004
*
* Time Since creates a string which friendly tells you the time since the
* original date Based on the original time_since() function by
* Natalie Downe - http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
*
* Copyright (c) 2004 Mark Wubben - http://neo.dzygn.com/
*
* Usage: date.toTimeSinceString(number nLimit, string sBetween, string sLastBetween)
* nLimit: limit the shown time units (year, month etc). default = 2
* sBetween: string between two time units. default = ", "
* sLastBetween: string between the second-last and last time unit.
*               default = " and "
=========================================================================*/
Date.prototype.toTimeSinceString = function(nLimit, sBetween, sLastBetween){
    if(!nLimit){ nLimit = 2; }
    if(!sBetween){ sBetween = ", "; }
    if(!sLastBetween){ sLastBetween = gettext(" and "); }
    if(!Date.prototype.toTimeSinceString._collStructs){
    	Date.prototype.toTimeSinceString._collStructs = new Array(
    		{seconds: 60 * 60 * 24 * 365, name: gettext("year"), plural: gettext("years")},
    		{seconds: 60 * 60 * 24 * 30, name: gettext("month"), plural: gettext("months")},
    		{seconds: 60 * 60 * 24 * 7, name: gettext("week"), plural: gettext("weeks")},
    		{seconds: 60 * 60 * 24, name: gettext("day"), plural: gettext("days")},
    		{seconds: 60 * 60, name: gettext("hour"), plural: gettext("hours")},
    		{seconds: 60, name: gettext("minute"), plural: gettext("minutes")}
    	);
    }

    var collStructs = Date.prototype.toTimeSinceString._collStructs;
    var nSecondsRemain = ((new Date).valueOf() - this.valueOf()) / 1000;
    var sReturn = "";
    var nCount = 0;
    var nFloored;

    for(var i = 0; i < collStructs.length && nCount < nLimit; i++){
    	nFloored = Math.floor(nSecondsRemain / collStructs[i].seconds);
    	if(nFloored > 0){
    		if(sReturn.length > 0){
    			if(nCount == nLimit - 1 || i == collStructs.length - 1){
    				sReturn += sLastBetween;
    			} else if(nCount < nLimit && i < collStructs.length){
    				sReturn += sBetween;
    			}
    		}
    		if(nFloored > 1){
    			sReturn += nFloored + " " + collStructs[i].plural;
    		} else {
    			sReturn += nFloored + " " + collStructs[i].name;
    		}
    		nSecondsRemain -= nFloored * collStructs[i].seconds;
    		nCount++;
    	}
    }

    return sReturn;
}


function procAllTimeSince() {
    elst = YAHOO.util.Dom.getElementsByClassName('datetime', 'span');
    for(var i=0; i < elst.length; i++){
        el = elst[i];
        timestamp_el = YAHOO.util.Dom.getElementsByClassName('timestamp', 'span', el)[0];
    	timestamp = new Number(timestamp_el.innerHTML);
        dateobj = new Date();
        dateobj.setTime(timestamp);
        tdisp = dateobj.toTimeSinceString();
        if(tdisp == '') {
            /* blank values indicate a future time... */
            el.innerHTML = gettext('just now');
        } else {
            el.innerHTML = interpolate(gettext('%s ago'), [tdisp]);
        }
    }
}

function get_ta() {
    return document.getElementById('add_post_div').elements['post'];
}

function surround(tag, ctag) {
    var ta = get_ta();
    if (!ctag) {
        ctag = tag;
    }
    if (document.selection) {
        ta.focus();
        var selection = document.selection.createRange();
        selection.text = tag + selection.text + ctag;
    } else if (ta.selectionStart >= 0) {
        var val = ta.value;
        ta.value = val.substring(0, ta.selectionStart) + tag + val.substring(ta.selectionStart, ta.selectionEnd) + ctag + val.substring(ta.selectionEnd, val.length);
    } else {
        ta.value += tag + ctag
    }
    return false;
}

function do_prefix(tag) {
    var ta = get_ta();
    if (document.selection) {
        ta.focus();
        var selection = document.selection.createRange();
        text = selection.text;
        selection.text = '\n' + tag + text.replace(/\n/g,'\n' + tag) + '\n';
    } else if (ta.selectionStart >= 0) {
        var val = ta.value;
        pref = ta.selectionStart && val.substring(ta.selectionStart - 1, ta.selectionStart) != '\n' ? '\n' : '';
        ta.value = val.substring(0, ta.selectionStart) + pref + tag + val.substring(ta.selectionStart, ta.selectionEnd).replace(/\n/g, '\n' + tag) + '\n' + val.substring(ta.selectionEnd, val.length);
    } else {
        ta.value += '\n' + tag;
    }
    return false;
}

function do_insert(tag) {
    var ta = get_ta();
    if (document.selection) {
        ta.focus();
        var selection = document.selection.createRange();
        text = selection.text;
        selection.text = tag;
    } else if (ta.selectionStart >= 0) {
        var val = ta.value;
        ta.value = val.substring(0, ta.selectionStart) + tag + val.substring(ta.selectionEnd, val.length);
    } else {
        ta.value += '\n' + tag;
    }
    return false;
}

function insert_img(url, name, title) {
    if (!url) {
        url = prompt(gettext('What is the URL of the image?'), 'http://');
        if (!url) {
            return false;
        }
    }
    if (!name) {
        name = prompt(gettext('What is the title of the image?'));
        if (!name) {
            name = '';
        }
    }
    if (!title) {
        title = name;
    }
    if (SNAP_POST_FILTER == 'markdown') {
        return do_insert('![' + name + '](' + url + ' "' + title + '")');
    } else {
        return do_insert('[img' + (name ? '=' + name : '') + ']' + url + '[/img]')
    }
}

function insert_link(url, name, title) {
    if (!url) {
        url = prompt(gettext('What is the URL of the link?'), 'http://');
        if (!url) {
            return false;
        }
    }
    if (!name) {
        name = prompt(gettext('What is the title of the link?'));
        if (!name) {
            name = url;
        }
    }
    if (!title) {
        title = name;
    }
    if (SNAP_POST_FILTER == 'markdown') {
        return do_insert('[' + name + '](' + url + ' "' + title + '")');
    } else {
        return do_insert('[url=' + url + ']' + name + '[/url]')
    }
}

function find_textarea (el) { return true; }// el.tagName.toLowerCase() == 'textarea'; }
function find_author (el) { return el.className == 'popup' && el.title == 'Author'; }

//function do_quote(anchor) {
//    if (!anchor) {
//        return false;
//    }
//    msg_div = anchor.parentNode.parentNode.parentNode.parentNode;
//    text = YAHOO.util.Dom.getElementsBy(find_textarea, 'textarea', msg_div)[0].value;
//    if (SNAP_POST_FILTER == 'markdown') {
//        get_ta().value += '> ' + text.replace(/\n/g, '\n> ');
//    } else {
//        author = YAHOO.util.Dom.getElementsBy(find_author, 'span', msg_div)[0].innerHTML;
//        get_ta().value += '[quote=' + author + ']' + text + '[/quote]\n';
//    }
//    return true;
//}

function do_quote(id) {
    var callback = function (author, text) {
        if (SNAP_POST_FILTER == 'markdown') {
            get_ta().value += '> ' + text.replace(/\n/g, '\n> ');
        } else {
            get_ta().value += '[quote=' + author + ']' + text + '[/quote]\n';
        }
    };
    get_post_to_quote(id, callback);
    return true;
}

// vim: ai ts=4 sts=4 et sw=4
