function parseCSV(text) {
  var rows=[], row=[], cell='', inQ=false;
  var CR=13, LF=10, COMMA=44, QUOTE=34;
  for (var i=0; i<=text.length; i++) {
    var c = i<text.length ? text.charCodeAt(i) : LF;
    if (inQ) {
      if (c===QUOTE && i+1<text.length && text.charCodeAt(i+1)===QUOTE) { cell+='"'; i++; }
      else if (c===QUOTE) { inQ=false; }
      else { cell+=text[i]; }
    } else {
      if (c===QUOTE) { inQ=true; }
      else if (c===COMMA) { row.push(cell); cell=''; }
      else if (c===LF || c===CR) {
        if (c===CR && i+1<text.length && text.charCodeAt(i+1)===LF) i++;
        row.push(cell); cell='';
        if (row.join('').trim()!=='') rows.push(row);
        row=[];
      } else { cell+=text[i]; }
    }
  }
  return rows;
}

function runEnrich(text) {
  var apiKey = '';
  var kEl = document.getElementById('apiKeyInput');
  if (kEl) apiKey = kEl.value.trim();

  var rows = parseCSV(text);
  if (rows.length < 2) { alert('CSV empty. Rows found: ' + rows.length); return; }

  var headers = rows[0].map(function(h) { return h.toLowerCase().trim(); });
  var ti = headers.indexOf('title');
  var ai = headers.indexOf('author');
  if (ti===-1 || ai===-1) { alert('Need title and author columns. Found: ' + headers.join(', ')); return; }

  var data = [];
  for (var d=1; d<rows.length; d++) {
    if ((rows[d][ti]||'').trim()) data.push(rows[d]);
  }
  var total = data.length;
  if (total===0) { alert('No data rows found'); return; }

  document.getElementById('progressBox').classList.add('active');
  document.getElementById('downloadBtn').style.display = 'none';
  document.getElementById('progressFill').style.width = '0%';
  document.getElementById('progressCount').textContent = '0 / ' + total;
  document.getElementById('progressLabel').textContent = 'Starting...';

  var outH = ['title','author','isbn','publisher','published_year','pages','genre','summary','cover_url','google_books_id'];
  var results = [];

  function next(i) {
    if (i >= total) {
      document.getElementById('progressLabel').textContent = 'Done! ' + total + ' books processed.';
      document.getElementById('progressFill').style.width = '100%';
      var lines = [outH.join(',')];
      for (var k=0; k<results.length; k++) {
        var r = results[k];
        lines.push(outH.map(function(h) {
          return '"' + (r[h]||'').split('"').join('""') + '"';
        }).join(','));
      }
      var blob = new Blob([lines.join('\n')], { type: 'text/csv' });
      var btn = document.getElementById('downloadBtn');
      btn.href = URL.createObjectURL(blob);
      btn.download = 'enriched_books.csv';
      btn.style.display = 'block';
      return;
    }
    var title = (data[i][ti]||'').trim();
    var author = (data[i][ai]||'').trim();
    document.getElementById('progressCount').textContent = (i+1) + ' / ' + total;
    document.getElementById('progressFill').style.width = Math.round(((i+1)/total)*100) + '%';
    document.getElementById('progressLabel').textContent = 'Looking up: ' + title.substring(0,35);
    var enc = encodeURIComponent;
    var q = 'intitle:' + enc(title) + (author ? '+inauthor:' + enc(author) : '');
    var url = 'https://www.googleapis.com/books/v1/volumes?q=' + q + '&maxResults=1&langRestrict=en' + (apiKey ? '&key=' + enc(apiKey) : '');
    var enriched = { title:title, author:author, isbn:'', publisher:'', published_year:'', pages:'', genre:'', summary:'', cover_url:'', google_books_id:'' };
    fetch(url)
      .then(function(r) { return r.json(); })
      .then(function(json) {
        var items = json.items || [];
        if (items.length) {
          var vol = items[0].volumeInfo || {};
          var isbns = vol.industryIdentifiers || [];
          var i13='', i10='';
          for (var j=0; j<isbns.length; j++) {
            if (isbns[j].type==='ISBN_13') i13=isbns[j].identifier;
            else if (isbns[j].type==='ISBN_10') i10=isbns[j].identifier;
          }
          var img = vol.imageLinks || {};
          enriched.title = vol.title || title;
          enriched.author = (vol.authors || [author]).join(', ');
          enriched.isbn = i13 || i10;
          enriched.publisher = vol.publisher || '';
          enriched.published_year = (vol.publishedDate||'').substring(0,4);
          enriched.pages = String(vol.pageCount||'');
          enriched.genre = (vol.categories||[]).join(', ');
          enriched.summary = (vol.description||'').substring(0,800);
          enriched.cover_url = (img.thumbnail||img.smallThumbnail||'').split('http://').join('https://');
          enriched.google_books_id = items[0].id || '';
        }
        results.push(enriched);
        next(i+1);
      })
      .catch(function(err) {
        enriched.summary = 'ERROR: ' + err.message;
        results.push(enriched);
        next(i+1);
      });
  }
  next(0);
}

// Wire up using addEventListener - more reliable than inline onchange
document.addEventListener('DOMContentLoaded', function() {
  var input = document.getElementById('enrichFile');
  if (input) {
    input.addEventListener('change', function() {
      if (!input.files || !input.files.length) return;
      // Reset value so same file can be selected again
      var reader = new FileReader();
      reader.onload = function(e) { runEnrich(e.target.result); };
      reader.onerror = function() { alert('Could not read file'); };
      reader.readAsText(input.files[0]);
      // Reset so same file triggers change next time
      input.value = '';
    });
  }
});

// Also expose startEnrich for backward compat
function startEnrich(input) {
  if (!input.files || !input.files.length) return;
  var reader = new FileReader();
  reader.onload = function(e) { runEnrich(e.target.result); };
  reader.onerror = function() { alert('Could not read file'); };
  reader.readAsText(input.files[0]);
}