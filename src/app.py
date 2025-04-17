from flask import Flask
from src.config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH, MODEL_PATH
from src.models import load_model
from src.routes import register_routes

def create_app():
    # Initialize Flask app
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = 'soumia_loves_mammography_classification'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    
    # Load model
    model = load_model(MODEL_PATH)
    
    # Register routes
    register_routes(app, model, UPLOAD_FOLDER)
    
    # Register error handlers
    @app.errorhandler(413)
    def too_large(e):
        from flask import flash, redirect, url_for
        flash('File too large (max 32MB)')
        return redirect(url_for('home'))

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('404.html'), 404
    
    return app