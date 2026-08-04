(function(){
  'use strict';
  document.documentElement.classList.add('inkdesk');
  window.addEventListener('pageshow',function(){document.body && document.body.classList.add('office-product-ready')},{once:true});
})();
