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

  var outH = ['title','author','isbn','publisher','published_year','pages','genre','summary','cover_url','open_library_id'];
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

    var enriched = { title:title, author:author, isbn:'', publisher:'', published_year:'', pages:'', genre:'', summary:'', cover_url:'', open_library_id:'' };

    // Step 1: Search Open Library for the work key
    var searchUrl = 'https://openlibrary.org/search.json?title=' + encodeURIComponent(title) + '&author=' + encodeURIComponent(author) + '&limit=1&fields=key,title,author_name,isbn,publisher,first_publish_year,number_of_pages_median,subject,cover_i';

    fetch(searchUrl)
      .then(function(r) { return r.json(); })
      .then(function(json) {
        var docs = json.docs || [];
        if (!docs.length) { results.push(enriched); next(i+1); return; }
        var doc = docs[0];

        var isbns = doc.isbn || [];
        // Prefer 13-digit ISBN
        var isbn = '';
        for (var j=0; j<isbns.length; j++) { if (isbns[j].length===13) { isbn=isbns[j]; break; } }
        if (!isbn && isbns.length) isbn = isbns[0];

        var coverId = doc.cover_i;
        var coverUrl = coverId ? 'https://covers.openlibrary.org/b/id/' + coverId + '-M.jpg' : '';
        var subjects = doc.subject || [];
        var genre = subjects.slice(0,3).join(', ');
        var olKey = doc.key || ''; // e.g. /works/OL12345W

        enriched.title = doc.title || title;
        enriched.author = (doc.author_name || [author]).join(', ');
        enriched.isbn = isbn;
        enriched.publisher = (doc.publisher || [''])[0];
        enriched.published_year = String(doc.first_publish_year || '');
        enriched.pages = String(doc.number_of_pages_median || '');
        enriched.genre = genre;
        enriched.cover_url = coverUrl;
        enriched.open_library_id = olKey;

        // Step 2: Fetch description from the work page
        if (olKey) {
          fetch('https://openlibrary.org' + olKey + '.json')
            .then(function(r2) { return r2.json(); })
            .then(function(work) {
              var desc = work.description || '';
              if (typeof desc === 'object') desc = desc.value || '';
              enriched.summary = String(desc).substring(0, 800);
              results.push(enriched);
              next(i+1);
            })
            .catch(function() { results.push(enriched); next(i+1); });
        } else {
          results.push(enriched);
          next(i+1);
        }
      })
      .catch(function(err) {
        enriched.summary = 'ERROR: ' + err.message;
        results.push(enriched);
        next(i+1);
      });
  }

  next(0);
}

document.addEventListener('DOMContentLoaded', function() {
  var input = document.getElementById('enrichFile');
  if (input) {
    input.addEventListener('change', function() {
      if (!input.files || !input.files.length) return;
      var reader = new FileReader();
      reader.onload = function(e) { runEnrich(e.target.result); };
      reader.onerror = function() { alert('Could not read file'); };
      reader.readAsText(input.files[0]);
      input.value = '';
    });
  }
});
