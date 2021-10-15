$(function() {
  $(".filter-form").submit(function(event) {
    event.preventDefault();
    var form = $('form');

    // if(history.pushState){
    //   window.history.replaceState("", "", "/?" + form.serialize());
    // }

    console.log(form.attr("method"))
    console.log(form.attr("action"))
    console.log(form.serialize() + "&ajax=1")

    $.ajax({
      type: "GET",
      url: "/filter",
      data: form.serialize() + "&ajax=1",
      success: function(response) {
        console.log(response);
    },
      error: function(error) {
        console.log(error);
    }
    });//.done(function(data) {
        // $(".card-wrapper").empty().append($(data).hide().fadeIn(500));
    // });

  });
});
