# JavaScript Bookmarklet Injection (`javascript:` protocol)

A technique to execute arbitrary JavaScript in the browser's page context, bypassing CORS restrictions and inheriting all auth cookies.

## Why This Works

Pasting `javascript:...` into the browser address bar and pressing Enter runs the code **in the current page's origin**. This means:

- ✅ All cookies from the current domain are available (no CORS issues)
- ✅ `fetch()` calls with `credentials: "include"` work automatically
- ✅ Can modify the DOM, read page data, call internal APIs
- ✅ No DevTools console needed (bypasses console autocomplete quirks)

This is fundamentally different from running code in DevTools Console (which has a different security context for some APIs) or via `data:` URLs (which create a new origin).

## When to Use

- **Site has an internal API** but the public endpoint requires auth cookies
- **Paginated content** where manual scrolling would take too long
- **Data extraction** from a site you're already logged into via the browser
- **CORS blocks** your fetch from WSL/Linux to the site's API

## Template

```javascript
javascript:(async()=>{
  // Your code here — runs in page context with full auth
  let r = await fetch("https://api.example.com/data?page=1", {credentials:"include"});
  let d = await r.json();
  // Display result on page
  document.body.innerHTML = "<pre>" + JSON.stringify(d, null, 2) + "</pre>";
  document.title = "DONE";
})()
```

## Limitations

- **Chrome strips `javascript:` from pasted URLs** on some versions. Workaround: type `javascript:` manually, then paste the rest.
- **Single-line only** (address bar doesn't support multi-line). Use `;` and arrow functions to compress.
- **Size limit**: Chrome address bar has ~64KB limit — fine for most scripts.
- **No debugging**: Unlike DevTools, you can't set breakpoints. Use `console.log()` and check Console tab.
- **Download/redirect blocked**: Chrome blocks navigation from `javascript:` URLs for file downloads and certain redirects.

## Common Patterns

### Batch API Fetch
```javascript
javascript:(async()=>{let all=[];for(let p=1;p<=5;p++){let r=await fetch("/api/items?page="+p,{credentials:"include"});let d=await r.json();all.push(...d.items)}document.body.innerHTML="<pre>"+all.map(x=>x.name).join("\n")+"</pre>"})()
```

### DOM Extraction
```javascript
javascript:(()=>{let items=[...document.querySelectorAll(".item-name")];document.body.innerHTML="<pre>"+items.map((e,i)=>(i+1)+". "+e.textContent).join("\n")+"</pre>"})()
```

### Copy to Clipboard (from page context, which works)
```javascript
javascript:(async()=>{let d=await(await fetch("/api/data")).json();let t=JSON.stringify(d);await navigator.clipboard.writeText(t);document.body.innerHTML="<pre>Copied "+t.length+" chars</pre>"})()
```

## Security Note

The `javascript:` protocol executes in the page origin. This means:
- It has full access to the page's DOM, cookies, localStorage, etc.
- It can make authenticated API calls on your behalf
- Don't paste untrusted bookmarklets into your address bar
