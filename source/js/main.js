// JQUERY READY
// ====================================
// ====================================
$(function() {




  // RWD Tables
  // ====================================
  // Modified version of Foundation's RWD Tables
  // http://zurb.com/playground/responsive-tables
  if( $('.js-table--rwd')) {
    var $rwdTable = $('.js-table--rwd');
    var $rwdBP = 960;
    var switched = false;

    var $rwd = 'ko-table--rwd';
    var $rwdWrap = 'ko-table__wrapper';
    var $rwdPinned = 'ko-table--pinned';
    var $rwdScrollable = 'ko-table--scrollable';

    var $rwdWrapSelector = '.' + $rwdWrap;
    var $rwdPinnedSelector = '.' + $rwdPinned;
    var $rwdScrollableSelector = '.' + $rwdScrollable;


    // Make Tables RWD
    var updateTables = function() {
      if (($(window).width() < $rwdBP) && !switched ){
        switched = true;
        $rwdTable.each(function(i, element) {
          splitTable($(element));
        });
        return true;
      }
      else if (switched && ($(window).width() > $rwdBP)) {
        switched = false;
        $rwdTable.each(function(i, element) {
          unsplitTable($(element));
        });
      }
    };


  $(window).load(updateTables);
  $(window).on("redraw",function(){switched=false;updateTables();}); // An event to listen for
  $(window).on("resize", updateTables);

  // Split Table
  function splitTable(original)
  {
    original.wrap("<div class='" + $rwdWrap + "' />");

    var copy = original.clone();
    copy.find("td:not(:first-child), th:not(:first-child)").css("display", "none");
    copy.removeClass($rwd);

    original.closest($rwdWrapSelector).append(copy);
    copy.wrap("<div class='" + $rwdPinned  + "' />");
    original.wrap("<div class='" + $rwdScrollable + "' />");

    // find width of pinned div
    var pinnedWidth = copy.width();
    original.css('margin-left', pinnedWidth);

    // setCellHeights(original, copy);
  }

  function unsplitTable(original) {
    original.closest($rwdWrapSelector).find($rwdPinnedSelector).remove();
    original.unwrap();
    original.unwrap();
    original.css('margin-left', '');
  }

  }; // rwd-tables


}); // Ready








// Modal Videos
// ====================================
$(function(){
  var $triggers = $('.js-video__trigger');
  var $closeVideo = $('#js-video__close');
  var $body = $('body');
  var $html = $('html');
  var videoClass = 'video--is-playing'

  $triggers.click(function(){
    var $target = $(this);
    var vidData = getData($target);
    $body.addClass(videoClass);

    // Disable scroll on HTML element when active
    $html.css('overflow-y', 'hidden');
    playVideo(vidData);
  });

  // Close modal. Stop video
  $closeVideo.click(function(){
    $body.removeClass(videoClass);
    $('#js-video__element').attr('src', '');
    $html.css('overflow-y', 'scroll');
  });

});


// Get the data from html element
var getData = function(target) {
  var vidData = target.data('video');
  var vidText = target.data('text');
  var data = {};
  return data = {
    data: vidData,
    text: vidText
  }
}


 // <iframe width="560" height="315" src="https://www.youtube.com/embed/W763P0hq5nM" frameborder="0" allowfullscreen></iframe>

// https://s3.amazonaws.com/gcstaublin-alyx/

// Update the Src of the video
var playVideo = function(target){
  // var urlBase = 'https://s3.amazonaws.com/hudl-internal-assets/alyx3/';
  var urlBase = 'https://www.youtube.com/embed/';
  // var urlEnd = '.mov';
  var urlEnd = '?autoplay=1;?rel=0&amp;controls=0&amp;showinfo=0';
  var urlTarget = target.data;
  var videoTarget = $('#js-video__element');
  var textTarget = $('#js-video__text');
  var videoURL = '';

  if(videoURL != '') {
    videoURL = '';
  } else {
      // videoURL += urlBase + urlTarget + urlEnd;
      videoURL += urlBase + urlTarget + urlEnd;
      videoTarget.attr('src', videoURL);
      textTarget.text(target.text);
  }
  // return videoURL;

}


