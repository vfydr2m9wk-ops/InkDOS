# Interface choice (Auto / Desktop / Smartphone) — legacy

Removed from the Settings (sun) menu and from Home on 2026-10-10 at the owner's request: the desktop density sizes
everything correctly on iPad, XeOS and Windows, and the mobile density only made the buttons a little larger.
`shared/ui-density.js` keeps its API and the `data-ui-density` attribute, but always resolves to `desktop`.

To bring the choice back, restore the pieces below.

`shared/ui-density.js`:

```js
function normalize(value){return VALID.has(value)?value:'auto'}
// at the end, with the other start-up code:
if(doc){if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',autoInstall,{once:true});else autoInstall();bootstrapWorkspaceSettings()}
```

`shared/localization/settings-strip.js` (the Interface section of the sun menu, the drawer strip button and its popover):

```js
 const density=root.InkDOSUiDensity;section('Interface');const row=doc.createElement('div');row.className='inkdos-settings-segment';for(const [mode,label] of [['auto','Auto'],['desktop','Desktop'],['mobile','Smartphone']]){const o=option(label,mode,()=>{density?.set?.(mode);for(const x of row.children)x.classList.toggle('active',x.dataset.settingsValue===(density?.preference||mode))});o.classList.toggle('active',mode===(density?.preference||'auto'));row.appendChild(o)}popover.appendChild(row);
```

```js
function showInterface(anchor){openPopover(anchor,'Interface');const api=root.InkDOSUiDensity;for(const [mode,label] of [['auto','Auto'],['desktop','Desktop'],['mobile','Smartphone']])popover.appendChild(option(label,mode,()=>{api?.set?.(mode);markActive('[data-settings-value]',api?.preference||mode);closePopover()}));markActive('[data-settings-value]',api?.preference||'auto')}
// in install(): strip.append(..., button('interface','↔','Interface'), ...)
// in toggle(): else if(kind==='interface')showInterface(anchor);
```
