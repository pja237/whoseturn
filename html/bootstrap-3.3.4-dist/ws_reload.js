
function refresh_hist(data) {
    $('#hist_list').empty();

    var row='';
    for(var i=0; i<data.length; i++) {
        row+='<tr>'
        for(var j=0; j<data[i].length; j++) {
            row+='<td>'+data[i][j];
        }
        row+='</td></tr>';
        $('#hist_list').append(row);
        row='';
    }
}


function refresh_orders(data,calling) {
    $('#order_list').empty();
    //alert('NEW ORDERS');

    var row='';
    console.log(' f: '+data+' '+calling);
    if(calling==1) {
        row+='<form action="/placeorder" method="POST">';
    }
    for(var i in data) {
        row+='<tr>'
        if(calling==1) {
            // add input box
            row+='<td><input type="checkbox" name="orderfor" value="'+i+'"></td>';
        }
        else {
            row+='<td></td>';
        }
        // user
        row+='<td>'+i+'</td>';
        for(var j=0; j<data[i].length; j++) {
            row+='<td>'+data[i][j]+'</td>';
        }
        row+='</tr>'
        $('#order_list').append(row);
        row='';
    }
}

function refresh_main(admin,data) {
    $('#main_list').empty();
    //alert('About to rebuild');
    var h_c1='<td class="info"><span class="glyphicon glyphicon-earphone" aria-hidden="true"></span> ';
    var h_c2='<td class="info">';
    var h_mc1='<td class="danger"><span class="glyphicon glyphicon-phone-alt" aria-hidden="true"></span> ';
    var h_mc2='<td class="danger">';

    var row='';
    //console.log(' f: '+admin+data);
    //console.log(' f: '+JSON.stringify(data));
    //console.log(' f: '+data["Pero"]);
    //console.log(' f: '+Object.keys(data));
    sorted_names= Object.keys(data).sort(function(a,b){return data[b][0]-data[a][0]});
    //console.log(typeof sorted_names);
    //console.log(' f: '+JSON.stringify(sorted_names));
    //console.log(' f: '+sorted_names.length);
    var max=data[sorted_names[0]][0];
    for(var j=0; j<sorted_names.length; j++) {
        //console.log(' fl: '+sorted_names[j]);
        i=sorted_names[j];
        //console.log(' f_LOOP: '+i+' : '+data[i]);
        row+='<tr>'
        if(data[i][1]==1) {
            row+=h_c1+i+'</td>'+h_c2+data[i][0]+'</td>';
        }
        else if (data[i][0]==max) {
            row+=h_mc1+i+'</td>'+h_mc2+data[i][0]+'</td>';
        }
        else {
            row+='<td>'+i+'</td><td>'+data[i][0]+'</td>';
        }
        row+='<td align="center">';
        if(admin==1) {
            row+='<a href="/user/'+i+'/increment"><span class="glyphicon glyphicon-plus" aria-hidden="true"></span></a>';
            row+='<a href="/user/'+i+'/decrement"><span class="glyphicon glyphicon-minus" aria-hidden="true"></span></a>';
        }
        row+='</td></tr>';
        $('#main_list').append(row);
        row='';
    }
}

var ws = new WebSocket("ws://192.168.56.207:8888/ws");
ws.onopen = function() {
    ws.send("Hello, world");
};
ws.onmessage = function (evt) {
    var data;
    console.log('GOT WS: '+evt.data);
    console.log('typeof WS: '+typeof(evt.data));
    var obj = JSON.parse(evt.data);
    console.log('POST PARSE oid: '+obj.oid);
    console.log('POST PARSE adm: '+obj.adm);
    console.log('POST PARSE data: '+obj.data);
    console.log('POST PARSE data stringify: '+JSON.stringify(obj.data));
    document.getElementById('ws_notification').innerHTML='AHA! SOMETHING HAPPENED! <strong> '+obj.who+' </strong> did something!';
    if(obj.oid=='REFRESH_MAIN') {
        refresh_main(obj.adm, obj.data);
    }
    else if(obj.oid=='REFRESH_HIST') {
        refresh_hist(obj.data);
    }
    else if(obj.oid=='REFRESH_ORDERS') {
        refresh_orders(obj.data, obj.calling);
    }
};

