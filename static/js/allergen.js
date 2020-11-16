$(function(){

  function allergen_change(){
    var cuisine_id = $("#cuisine").val();

    $.ajax({
      type: "GET",
      url: "/cuisine/" + cuisine_id
    }).done(function(data){
      $("#allergen").empty();
      if($("#cuisine").hasClass("category-filter")){
        $("#allergen").append(
          $("<option></option>").attr("value", "0").text(" --- ")
        );
      }
      $.each(data.allergens, function(index, value){
        $("#allergen").append(
          $("<option></option>").attr("value", value[0]).text(value[1])
        );
      });
    });
  }

  $("#cuisine").change(function(){
    allergen_change();
  });

  allergen_change();
});
