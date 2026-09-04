(function(global){
'use strict';const DEFAULT_LIMITS=Object.freeze({maxLength:4096,maxTokens:1024,maxDepth:64,maxSteps:10000});
class FormulaError extends Error{constructor(code,message){super(message);this.name='FormulaError';this.code=code}}function evaluateArithmetic(source,options={}){
  const limits=Object.assign({},DEFAULT_LIMITS,options.limits||{}),input=String(source||'').trim();
  if(input.length>limits.maxLength)throw new FormulaError('FORMULA_TOO_LONG','Formula exceeds the safe length limit.');
  let index=0,tokens=0,steps=0,current=null;
  function step(){if(++steps>limits.maxSteps)throw new FormulaError('STEP_LIMIT','Formula evaluation exceeded the safe step limit.');}
  function next(){step();while(/\s/.test(input[index]||''))index++;if(index>=input.length)return current={type:'eof'};if(++tokens>limits.maxTokens)throw new FormulaError('TOKEN_LIMIT','Formula contains too many tokens.');const start=index,ch=input[index];
    if(/[0-9.]/.test(ch)){const m=/^(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?/.exec(input.slice(index));if(!m)throw new FormulaError('INVALID_NUMBER','Invalid numeric literal.');index+=m[0].length;const value=Number(m[0]);if(!Number.isFinite(value))throw new FormulaError('INVALID_NUMBER','Non-finite numeric literal.');return current={type:'number',value};}
    if(/[A-Za-z_]/.test(ch)){const m=/^[A-Za-z_][A-Za-z0-9_.]*/.exec(input.slice(index));index+=m[0].length;return current={type:'identifier',value:m[0]};}
    if('+-*/%^()'.includes(ch)){index++;return current={type:ch,value:ch};}
    throw new FormulaError('INVALID_TOKEN','Unsupported token at position '+start+'.');
  }
  function errorValue(value){return typeof value==='string'&&value.startsWith('#')?value:''}
  function finite(value){const error=errorValue(value);if(error)return error;if(!Number.isFinite(value))throw new FormulaError('INVALID_RESULT','Formula produced a non-finite value.');return value}
  function primary(depth){if(depth>limits.maxDepth)throw new FormulaError('DEPTH_LIMIT','Formula nesting exceeds the safe limit.');step();if(current.type==='number'){const v=current.value;next();return v}if(current.type==='identifier'){const name=current.value;next();if(!options.resolveIdentifier)throw new FormulaError('UNSUPPORTED_IDENTIFIER','Unsupported identifier: '+name);const resolved=options.resolveIdentifier(name),error=errorValue(resolved);if(error)return error;const v=Number(resolved);if(!Number.isFinite(v))throw new FormulaError('INVALID_REFERENCE','Reference did not resolve to a finite number: '+name);return v}if(current.type==='('){next();const v=expression(depth+1);if(current.type!==')')throw new FormulaError('MALFORMED','Missing closing parenthesis.');next();return v}throw new FormulaError('MALFORMED','Expected a number or parenthesized expression.')}
  function unary(depth){if(current.type==='+'||current.type==='-'){const op=current.type;next();const v=unary(depth+1),error=errorValue(v);if(error)return error;return op==='-'?-v:v}return primary(depth)}
  function percentage(depth){let value=unary(depth);while(current.type==='%'){next();if(!errorValue(value))value=finite(value/100)}return value}
  function power(depth){let left=percentage(depth);if(current.type==='^'){next();const right=power(depth+1),error=errorValue(left)||errorValue(right);left=error||finite(left**right)}return left}
  function product(depth){let left=power(depth);while(['*','/'].includes(current.type)){const op=current.type;next();
    const right=power(depth),error=errorValue(left)||errorValue(right);if(error){left=error;continue}if(op==='/'&&right===0){left='#DIV/0!';continue}left=finite(op==='*'?left*right:left/right)}return left}
  function expression(depth){let left=product(depth);while(current.type==='+'||current.type==='-'){const op=current.type;next();
    const right=product(depth),error=errorValue(left)||errorValue(right);left=error||finite(op==='+'?left+right:left-right)}return left}
  next();if(current.type==='eof')throw new FormulaError('EMPTY','Formula is empty.');const result=expression(0);if(current.type!=='eof')throw new FormulaError('MALFORMED','Unexpected trailing formula input.');return result;
}global.InkDOSFormula=Object.freeze({DEFAULT_LIMITS,FormulaError,evaluateArithmetic});
})(typeof window!=='undefined'?window:globalThis);
