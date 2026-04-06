from flask import Flask, request, redirect, render_template_string
import sqlite3
import string, random
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
import os

app = Flask(__name__)

# Mode
LOCAL_MODE = True
REAL_DOMAIN = "https://yourtool.com"

# Database setup
def init_db():
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS links (short TEXT, original TEXT)")
    conn.commit()
    conn.close()

init_db()

def generate_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ShortLink Tool</title>
<style>
*{box-sizing:border-box;} 
body{margin:0;font-family:Arial;background:#f1f3f6;}
.container{max-width:420px;margin:10px auto;background:white;padding:15px;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.1);text-align:center;}
h2{margin:5px 0;} 
input{width:100%;padding:10px;border:1px solid #ccc;border-radius:5px;margin-top:8px;}
button{width:100%;padding:12px;margin-top:10px;background:#007bff;color:white;border:none;border-radius:5px;cursor:pointer;}
button:hover{background:#0056b3;}
.result{margin-top:10px;padding:8px;background:#f8f9fa;border-radius:5px;}
a{word-break:break-all;color:#28a745;font-weight:bold;text-decoration:none;}
img{margin-top:5px;}
.share-buttons{margin-top:10px;}
.share-buttons a{margin:0 5px;text-decoration:none;color:white;padding:8px 12px;border-radius:5px;}
.share-buttons .whatsapp{background:#25D366;}
.share-buttons .facebook{background:#3b5998;}
.share-buttons .twitter{background:#1DA1F2;}
@media(max-width:480px){.container{margin:5px;padding:10px;}}
</style>
</head>
<body>
<div class="container">
<h2>🔗 ShortLink Generator</h2>
<form method="POST">
<input type="text" name="url" placeholder="Paste your long URL..." required>
<button type="submit">Generate Link</button>
</form>

{% if short_url %}
<div class="result">
<p><b>Your Short Link:</b></p>
<input type="text" id="shortLink" value="{{short_url}}" readonly style="width:100%;padding:8px;border:1px solid #ccc;border-radius:5px;">
<button onclick="copyLink()" style="margin-top:8px;width:100%;padding:8px;background:#28a745;color:white;border:none;border-radius:5px;cursor:pointer;">Copy Link</button>

<p><b>QR Code (SVG):</b></p>
<img src="data:image/svg+xml;base64,{{qr}}" width="130">

<div class="share-buttons">
<p><b>Share:</b></p>
<a href="https://wa.me/?text={{short_url}}" target="_blank" class="whatsapp">WhatsApp</a>
<a href="https://www.facebook.com/sharer/sharer.php?u={{short_url}}" target="_blank" class="facebook">Facebook</a>
<a href="https://twitter.com/intent/tweet?url={{short_url}}" target="_blank" class="twitter">Twitter</a>
</div>
</div>

<script>
function copyLink() {
  var copyText = document.getElementById("shortLink");
  copyText.select();
  copyText.setSelectionRange(0, 99999);
  document.execCommand("copy");
  alert("Link copied to clipboard!");
}
</script>
{% endif %}
</div>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def home():
    short_url = None
    qr_img = None

    if request.method == "POST":
        original = request.form["url"]
        code = generate_code()

        # Save to DB
        conn = sqlite3.connect("links.db")
        c = conn.cursor()
        c.execute("INSERT INTO links VALUES (?,?)", (code, original))
        conn.commit()
        conn.close()

        # Base URL
        if LOCAL_MODE:
            base = request.host_url.rstrip("/")
        else:
            base = REAL_DOMAIN.rstrip("/")
            if not base.endswith(".com"):
                base += ".com"

        short_url = f"{base}/{code}"

        # SVG QR code
        factory = qrcode.image.svg.SvgImage
        img = qrcode.make(short_url, image_factory=factory)
        buffer = BytesIO()
        img.save(buffer)
        qr_img = base64.b64encode(buffer.getvalue()).decode()

    return render_template_string(HTML, short_url=short_url, qr=qr_img)

@app.route("/<code>")
def redirect_link(code):
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute("SELECT original FROM links WHERE short=?", (code,))
    result = c.fetchone()
    conn.close()

    if result:
        return redirect(result[0])
    return "Link not found!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)