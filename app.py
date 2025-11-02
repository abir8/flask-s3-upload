from flask import Flask, request, render_template_string
import boto3, os, uuid

app = Flask(__name__)
S3_BUCKET = os.environ.get("S3_BUCKET")
REGION = os.environ.get("AWS_REGION", "us-east-1")
s3 = boto3.client("s3", region_name=REGION)

HTML = """
<!doctype html><title>Upload</title><h1>Upload file</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=file>
  <input type=submit value=Upload>
</form>
{% if url %}<p>Uploaded: <a href="{{url}}">{{url}}</a></p>{% endif %}
"""

@app.route("/", methods=["GET","POST"])
def upload():
    url = None
    if request.method == "POST":
        f = request.files.get("file")
        if f:
            key = f"{uuid.uuid4().hex}_{f.filename}"
            s3.upload_fileobj(f, S3_BUCKET, key, ExtraArgs={"ACL":"public-read"})
            url = f"https://{S3_BUCKET}.s3.{REGION}.amazonaws.com/{key}"
    return render_template_string(HTML, url=url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
