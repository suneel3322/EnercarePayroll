jQuery(function () {
    $("#topnav a.my-courses-link").on("click", function () {
        $("#topnav").find(".dropdown-toggle").dropdown("hide");
    });
    $("#my-courses-modal a.my-courses-link").on("click", function () {
        $("#my-courses-modal").modal("hide");
    });
    $("a.my-courses-link").on("click", function () {
        let btn = $(this);
        if (btn.data("hasAcademy") === true && btn.data("hasInternal") === true) {
            $('#my-courses-modal').modal();
            return false;
        }
        let destination = null;
        if (btn.data("hasAcademy") === true) {
            destination = "academy";
        } else if (btn.data("hasInternal") === true) {
            destination = "internal";
        } else {
            console.error("User has neither academy nor internal course access");
            return false;
        }
        let targetWindow = window.open();
        let url = btn.data("myCoursesHref");
        if (typeof url === "undefined") {
            url = "login/myCourses.php";
        }
        $.ajax({
            type: "POST",
            url: url,
            data: {
                destination: destination,
                csrfTokenName: btn.data("tokenName"),
                csrfToken: btn.data("token"),
                ajax: 1
            },
            dataType: "json",
            success: function (response) {
                if (typeof response.error !== "undefined" &&
                    response.error === "csrf_failed" &&
                    document.location.pathname.match(/[^\/]+$/)[0] !== "error.php"
                ) {
                    targetWindow.location.href = "error.php?code=0001";
                    return;
                }
                btn.data("tokenName", response.csrfTokenName);
                btn.data("token", response.csrfToken);
                targetWindow.location.href = response.url;
            }
        });
    });
});
