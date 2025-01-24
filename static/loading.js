setInterval(function() {
    fetch("/check_status")
      .then(resp => resp.text())
      .then(responseText => {
        if (responseText === "done") {
          window.location.href = "/results";
        }
      });
  }, 2000);  