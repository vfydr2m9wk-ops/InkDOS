(function(g){'use strict';
const NS=g.InkDOS2=g.InkDOS2||{};
function create(){return {loaded:false,fileName:'Untitled.txt',encoding:'utf-8',bom:false,lineEnding:'\n',wrap:true,fontSize:16,session:new NS.DocumentSession(),history:new NS.TxtHistory(),openController:null,debounce:null,lastReceipt:null,metrics:null,discardResolver:null}}
NS.TxtState=Object.freeze({create});
})(globalThis);
