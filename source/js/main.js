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