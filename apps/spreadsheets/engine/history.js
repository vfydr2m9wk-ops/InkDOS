(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{};
class History{
 constructor(limit=80){this.limit=limit;this.undoStack=[];this.redoStack=[]}
 reset(){this.undoStack.length=0;this.redoStack.length=0}
 push(action){this.undoStack.push(action);if(this.undoStack.length>this.limit)this.undoStack.shift();this.redoStack.length=0}
 undo(apply){const a=this.undoStack.pop();if(!a)return false;apply(a,'undo');this.redoStack.push(a);return true}
 redo(apply){const a=this.redoStack.pop();if(!a)return false;apply(a,'redo');this.undoStack.push(a);return true}
 get canUndo(){return this.undoStack.length>0}get canRedo(){return this.redoStack.length>0}
}
NS.History=History;
})(globalThis);
