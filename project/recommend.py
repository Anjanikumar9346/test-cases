from flask import Flask, request, jsonify
from github import Github
from dotenv import load_dotenv
import os
import base64
import json
import openai

# ---------------- Load environment variables ----------------
load_dotenv("Jira_git.env")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_ORG = os.getenv("GITHUB_ORG")  # leave blank if you want all repos
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---------------- Setup clients ----------------
gh = Github(GITHUB_TOKEN)
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

# ---------------- Helper: get all repos ----------------
def get_all_repos():
    if GITHUB_ORG:
        org = gh.get_organization(GITHUB_ORG)
        return org.get_repos()
    else:
        return gh.get_user().get_repos()

# ---------------- Helper: search file across repos/branches ----------------
def find_file_in_github(filename):
    repos = get_all_repos()
    results = []
    for repo in repos:
        try:
            branches = repo.get_branches()
            for branch in branches:
                contents = repo.get_contents("", ref=branch.name)
                while contents:
                    file_content = contents.pop(0)
                    if file_content.type == "dir":
                        contents.extend(repo.get_contents(file_content.path, ref=branch.name))
                    else:
                        if file_content.name == filename:
                            results.append({
                                "repo": repo.full_name,
                                "branch": branch.name,
                                "path": file_content.path
                            })
        except Exception:
            continue
    return results

# ---------------- Helper: get file content ----------------
def get_file_content(repo_fullname, branch, path):
    repo = gh.get_repo(repo_fullname)
    file = repo.get_contents(path, ref=branch)
    content = base64.b64decode(file.content).decode("utf-8", errors="ignore")
    return content

# ---------------- Helper: get PDFs from same folder ----------------
def get_related_pdfs(repo_fullname, branch, folder):
    repo = gh.get_repo(repo_fullname)
    contents = repo.get_contents(folder, ref=branch)
    pdfs = []
    for file in contents:
        if file.type == "file" and file.name.endswith(".pdf"):
            try:
                pdf_content = base64.b64decode(file.content).decode("utf-8", errors="ignore")
            except Exception:
                pdf_content = "Binary PDF content (not decoded)"
            pdfs.append({
                "file_name": file.name,
                "content": pdf_content
            })
    return pdfs

# ---------------- Helper: call OpenAI ----------------
def get_recommendations(input_json):
    response = openai.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are a test case recommendation engine. Always return valid JSON."},
            {"role": "user", "content": f"Generate top {input_json['top_n']} recommended test cases based on this input:\n{json.dumps(input_json)}"}
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except:
        return {"error": "OpenAI returned invalid JSON", "raw": content}

# ---------------- API Endpoint ----------------
@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    filename = data.get("filename")
    top_n = data.get("top_n", 3)

    if not filename:
        return jsonify({"error": "Missing filename"}), 400

    # Step 1: Find file
    results = find_file_in_github(filename)
    if not results:
        return jsonify({"error": f"{filename} not found in any repo/branch"}), 404

    # Use first match (can be extended to show multiple)
    match = results[0]
    python_content = get_file_content(match["repo"], match["branch"], match["path"])

    # Step 2: Get related PDFs
    folder = os.path.dirname(match["path"])
    related_pdfs = get_related_pdfs(match["repo"], match["branch"], folder)

    # Step 3: Build input JSON for OpenAI
    input_json = {
        "python_file": {
            "file_name": filename,
            "content": python_content
        },
        "related_pdfs": related_pdfs,
        "top_n": top_n
    }

    # Step 4: Call OpenAI
    recommendations = get_recommendations(input_json)

    return jsonify(recommendations)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)

