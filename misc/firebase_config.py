# PCT GeoGuesser — Firebase web configuration
#
# Firebase web config is public by design (it ships in every page's JS);
# access control lives in firestore.rules, not in keeping these values secret.
# Source: Firebase console → Project settings → General → Your apps → Web app.

import json

FIREBASE_SDK_VERSION = "12.19.0"
FIREBASE_SDK_BASE    = f"https://www.gstatic.com/firebasejs/{FIREBASE_SDK_VERSION}"

FIREBASE_CONFIG = {
    "apiKey":            "AIzaSyD8HreF5tpB1sC_8w09V5g1IV2-O95uG54",
    "authDomain":        "pct-geoguesser-9d535.firebaseapp.com",
    "projectId":         "pct-geoguesser-9d535",
    "storageBucket":     "pct-geoguesser-9d535.firebasestorage.app",
    "messagingSenderId": "89928482559",
    "appId":             "1:89928482559:web:e3e055af16a7417e10d6ca",
}

FIREBASE_CONFIG_JS = json.dumps(FIREBASE_CONFIG)

# Firestore REST endpoint — lets pages do simple public reads without the SDK.
FIRESTORE_REST = (
    f"https://firestore.googleapis.com/v1/projects/{FIREBASE_CONFIG['projectId']}"
    f"/databases/(default)/documents"
)
FIRESTORE_REST_KEY = FIREBASE_CONFIG["apiKey"]

# <head> script applying site_settings/primary_font. The cached value is applied
# synchronously (no font flash); a background fetch refreshes it.
# Values: 'futura' (default) | 'open-sans'. Inserted into the pages' f-strings
# as a value, so braces here are single.
FONT_PREF_SCRIPT = """<script>
(function() {
  var STACKS = {
    'futura':    "'Futura', 'Futura PT', 'Open Sans', Arial, sans-serif",
    'open-sans': "'Open Sans', Arial, sans-serif"
  };
  function apply(val) {
    if (!STACKS[val]) return;
    document.documentElement.style.setProperty('--font-primary', STACKS[val]);
    try { localStorage.setItem('pct_font', val); } catch (_) {}
  }
  try { apply(localStorage.getItem('pct_font')); } catch (_) {}
  fetch('%s/site_settings/primary_font?key=%s')
    .then(function(r) { return r.ok ? r.json() : null; })
    .then(function(d) { if (d && d.fields && d.fields.value) apply(d.fields.value.stringValue); })
    .catch(function() {});
})();
</script>""" % (FIRESTORE_REST, FIRESTORE_REST_KEY)
