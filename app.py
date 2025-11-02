from flask import Flask, request, render_template_string, redirect, url_for, flash
import boto3, os, uuid
from dotenv import load_dotenv

# --- Load environment variables from .env ---
load_dotenv()  # looks for .env in project root

app = Flask(__name__)
app.secret_key = "supersecretkey"  # required for flash messages

# --- AWS S3 Configuration ---
S3_BUCKET = os.environ.get("S3_BUCKET")
REGION = os.environ.get("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

# --- Check configuration ---
if not S3_BUCKET:
    raise ValueError("S3_BUCKET environment variable not set. Please set it in .env or terminal.")

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise ValueError("AWS credentials not set. Configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")

# --- Initialize S3 client ---
s3 = boto3.client(
    "s3",
    region_name=REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# --- Bootstrap HTML Templates ---
UPLOAD_HTML = """ 
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Flask S3 Upload</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<div class="container py-5">
  <h2 class="text-center mb-4">Upload File to S3</h2>
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card p-4">
        <form method="post" enctype="multipart/form-data">
          <div class="mb-3">
            <input class="form-control" type="file" name="file" required>
          </div>
          <button type="submit" class="btn btn-primary w-100">Upload</button>
        </form>
        <a href="{{ url_for('list_files') }}" class="btn btn-link mt-3">View Uploaded Files</a>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="alert alert-info mt-3">
              {% for msg in messages %}
                <div>{{ msg }}</div>
              {% endfor %}
            </div>
          {% endif %}
        {% endwith %}
        {% if url %}
          <div class="alert alert-success mt-3">
            File uploaded successfully! <a href="{{ url }}" target="_blank">View File</a>
          </div>
        {% endif %}
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""

LIST_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Uploaded Files</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<div class="container py-5">
  <h2 class="text-center mb-4">Uploaded Files</h2>
  <div class="row justify-content-center">
    <div class="col-md-8">
      <div class="card p-4">
        <ul class="list-group">
          {% for file in files %}
          <li class="list-group-item d-flex justify-content-between align-items-center">
            {{ file }}
            <a href="https://{{ bucket }}.s3.{{ region }}.amazonaws.com/{{ file }}" target="_blank" class="btn btn-sm btn-outline-primary">View/Download</a>
          </li>
          {% else %}
          <li class="list-group-item text-muted">No files uploaded yet.</li>
          {% endfor %}
        </ul>
        <a href="{{ url_for('upload') }}" class="btn btn-link mt-3">Upload New File</a>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def upload():
    url = None
    if request.method == "POST":
        f = request.files.get("file")
        if not f:
            flash("No file selected!")
        else:
            key = f"{uuid.uuid4().hex}_{f.filename}"
            try:
                s3.upload_fileobj(f, S3_BUCKET, key)
                url = f"https://{S3_BUCKET}.s3.{REGION}.amazonaws.com/{key}"
            except Exception as e:
                flash(f"Upload failed: {str(e)}")
    return render_template_string(UPLOAD_HTML, url=url)

@app.route("/files")
def list_files():
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET)
        files = [obj['Key'] for obj in response.get('Contents', [])]
    except Exception as e:
        flash(f"Could not list files: {str(e)}")
        files = []
    return render_template_string(LIST_HTML, files=files, bucket=S3_BUCKET, region=REGION)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
