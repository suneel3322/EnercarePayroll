function BatmoAudioPop(filedesc, filepath, WindowNumber, extension) {

    // Get Operating System
    const isWin = navigator.userAgent.toLowerCase().indexOf("windows") != -1;
    if (isWin) { // Use MIME type = "application/x-mplayer2"
        visitorOS = "Windows";
    } else { // Use MIME type = "audio/mpeg"; // or audio/x-wav or audio/x-ms-wma, etc.
        visitorOS = "Other";
    }

    // Get the MIME type of the audio file from its extension (for non-Windows browsers)
    let mimeType = "audio/mpeg"; // assume MP3/M3U
    let objTypeTag = "application/x-mplayer2"; // The Windows MIME type to load the WMP plug-in in Firefox, etc.

    if (extension === ".wav") {
        mimeType = "audio/x-wav"
    }
    if (extension === ".aiff") {
        mimeType = "audio/x-aiff"
    }
    if (extension === ".wma") {
        mimeType = "audio/x-ms-wma"
    }
    if (extension === ".mid") {
        mimeType = "audio/mid"
    }
    // Add additional MIME types as desired

    objTypeTag = mimeType; // audio/mpeg, audio/x-wav, audio/x-ms-wma, etc.};
    let PlayerWin = window.open('', WindowNumber, 'width=320,height=217,top=0,left=0,screenX=0,screenY=0,resizable=0,scrollbars=0,titlebar=0,toolbar=0,menubar=0,status=0,directories=0');
    PlayerWin.focus();
    PlayerWin.document.writeln("<html><head><title>" + filedesc + "</title></head>");
    PlayerWin.document.writeln("<body bgcolor='#f4faff'>"); // specify background img if desired
    PlayerWin.document.writeln("<div align='center' style='color:#1f75cc;'>");
    PlayerWin.document.writeln("<b style ='font-size:18px;font-family:Lucida,sans-serif;line-height:1.6'>" + filedesc + "</b><br />");

    const is_chrome = navigator.userAgent.toLowerCase().indexOf('chrome') > -1;
    const is_firefox = navigator.userAgent.toLowerCase().indexOf('firefox') > -1;

    if (is_chrome || is_firefox) {

        PlayerWin.document.writeln("<audio controls src='" + filepath + "' type='" + mimeType + "'>");
        PlayerWin.document.writeln("Your browser does not support the audio element.");
        PlayerWin.document.writeln("</audio>")

    } else {

        PlayerWin.document.writeln("<object width='280' height='69'>");
        PlayerWin.document.writeln("<param name='src' value='" + filepath + "'>");
        PlayerWin.document.writeln("<param name='type' value='" + objTypeTag + "'>");
        PlayerWin.document.writeln("<param name='autostart' value='1'>");
        PlayerWin.document.writeln("<param name='showcontrols' value='1'>");
        PlayerWin.document.writeln("<param name='showstatusbar' value='1'>");
        PlayerWin.document.writeln("<embed src ='" + filepath + "' type='" + objTypeTag + "' autoplay='true' width='280' height='69' controller='1' showstatusbar='1' bgcolor='#f4faff' kioskmode='true'>");
        PlayerWin.document.writeln("</embed></object>");
    }

    PlayerWin.document.writeln("</div><div id='ajax'><p></p></div>");

    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (xhttp.readyState == 4 && xhttp.status == 200) {
            PlayerWin.document.getElementById("ajax").innerHTML = "<p style='font-size:12px;font-family:Lucida,sans-serif;text-align:center'><a href='" + filepath + "'>Download this file</a> <span style='font-size:10px'>(right-click    or Control-click)</span></p>";
        }
    };
    xhttp.open("GET", "include/getUserlevel.php", true);
    xhttp.send();

    PlayerWin.document.writeln("<form><div align='center'><input type='button' value='Close this window' onclick='window.close();'></div></form>");
    PlayerWin.document.writeln("</body></html>");
    PlayerWin.document.close(); // "Finalizes" new window
}