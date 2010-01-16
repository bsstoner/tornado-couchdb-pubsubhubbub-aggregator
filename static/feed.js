$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    updater.poll();
});

var updater = {
    errorSleepTime: 500,
    cursor: null,

    poll: function() {
	//if (updater.cursor) args.cursor = updater.cursor;
	$.ajax({url: "/feeds/getupdates", type: "POST", dataType: "text",
		data: "", success: updater.onSuccess,
		error: updater.onError});
    },

    onSuccess: function(response) {
	try {
	    updater.newMessages(eval("(" + response + ")"));
	} catch (e) {
	    updater.onError();
	    return;
	}
	updater.errorSleepTime = 500;
	window.setTimeout(updater.poll, 0);
    },

    onError: function(response) {
	updater.errorSleepTime *= 2;
	//console.log("Poll error; sleeping for", updater.errorSleepTime, "ms");
	window.setTimeout(updater.poll, updater.errorSleepTime);
    },

    newMessages: function(response) {
	if (!response.messages) return;
	updater.cursor = response.cursor;
	var messages = response.messages;
	updater.cursor = messages[messages.length - 1]._id;
	//console.log(messages.length, "new messages, cursor:", updater.cursor);
	for (var i = 0; i < messages.length; i++) {
	    updater.showMessage(messages[i],800+(i*800));
	}
    },

    showMessage: function(message,delay) {
	var existing = $("#m" + message._id);
	if (existing.length > 0) return;
	var messagehtml = "<li id='" + message._id + "' style='display:none'><a href='" + message.link + "'>" + message.title + "</a></li>";
	$("#entries").prepend(messagehtml);
	i = window.setTimeout("slideEntry('#" + message._id + "');",delay);
    }
};

function slideEntry(obj_id){
	$(obj_id).slideDown(800);
	return false;
}

var timeout_handles = []    
function set_time_out( id, code, time ) /// wrapper
{
        if( id in timeout_handles )
        {
                clearTimeout( timeout_handles[id] )
        }

        timeout_handles[id] = setTimeout( code, time )
}
