from flask import render_template

def page_not_found(error):
    return render_template("page_not_found.html"), 404